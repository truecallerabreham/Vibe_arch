import json
from backend.app.config import settings
from backend.app.models.ast import SymbolGraph
from backend.app.models.architecture import Architecture, Component, Relationship, Confidence
from backend.app.models.repo import FileTree


class LLMInterpreter:
    """LLM-powered architecture interpreter. Takes AST facts + file tree + README, produces architecture."""

    def __init__(self):
        self.provider = settings.llm_provider

    async def interpret(self, repo_url: str, repo_name: str, readme: str,
                        file_tree: FileTree, ast_graphs: dict[str, SymbolGraph]) -> Architecture:
        """Interpret repo architecture from AST facts + file tree + README."""
        prompt = self._build_prompt(repo_name, readme, file_tree, ast_graphs)
        response = await self._call_llm(prompt)
        return self._parse_response(repo_url, response)

    def _build_prompt(self, repo_name: str, readme: str, file_tree: FileTree,
                      ast_graphs: dict[str, SymbolGraph]) -> str:
        """Build a structured prompt for the LLM."""
        tree_lines = []
        self._flatten_tree(file_tree.root, tree_lines, 0)
        tree_str = "\n".join(tree_lines[:80])

        ast_summary = self._summarize_ast(ast_graphs)

        prompt = f"""You are an expert software architect analyzing a GitHub repository.

Repository: {repo_name}

## README Summary
{readme[:2000]}

## File Structure (top-level)
{tree_str}

## AST Facts (symbols and imports)
{ast_summary[:2000]}

## Task
Analyze this repository's architecture. Produce a JSON object with:
1. Components (logical groupings of related files that serve a purpose)
2. Relationships (how components connect: depends_on, contains, communicates_with)

Rules:
- Every component MUST have a "path" that exists in the file structure above
- Group related files into components (e.g., src/auth/ -> Authentication Module)
- Describe each component's role in 1-2 sentences
- Be conservative with relationships - only include what you have evidence for
- If uncertain about a relationship, mark confidence as "inferred" not "verified"

Return ONLY valid JSON matching this schema:
{{
  "components": [
    {{"id": "string", "name": "string", "role": "string", "path": "string", "confidence": "verified|inferred|unverifiable", "children": ["string"]}}
  ],
  "relationships": [
    {{"source_id": "string", "target_id": "string", "type": "string", "confidence": "verified|inferred|unverifiable"}}
  ]
}}"""
        return prompt

    def _flatten_tree(self, node, lines, depth):
        """Flatten FileTree to indented text lines."""
        indent = "  " * depth
        if node.type == "file":
            lines.append(f"{indent}{node.path.split('/')[-1]}")
        else:
            lines.append(f"{indent}{node.path.split('/')[-1] if node.path else '/'}")
            for child in node.children:
                self._flatten_tree(child, lines, depth + 1)

    def _summarize_ast(self, ast_graphs: dict[str, SymbolGraph]) -> str:
        """Summarize AST graphs into readable text."""
        lines = []
        for file_path, graph in ast_graphs.items():
            symbols = [f"{s.type}:{s.name}(L{s.line_number})" for s in graph.symbols[:5]]
            imports = [f"-> {i.to_path}" for i in graph.imports[:5]]
            if symbols or imports:
                lines.append(f"\n{file_path}:")
                if symbols:
                    lines.append(f"  Symbols: {', '.join(symbols)}")
                if imports:
                    lines.append(f"  Imports: {', '.join(imports)}")
        return "\n".join(lines[:100])

    async def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM provider."""
        if self.provider == "glm":
            return await self._call_glm(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        else:
            return await self._call_openai(prompt)

    async def _call_glm(self, prompt: str) -> str:
        """Call ZhipuAI GLM API."""
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=settings.glm_api_key)
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    def _parse_response(self, repo_url: str, response: str) -> Architecture:
        """Parse LLM response into Architecture model."""
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)
        components = [Component(**c) for c in data.get("components", [])]
        relationships = [Relationship(**r) for r in data.get("relationships", [])]

        return Architecture(
            repo_url=repo_url,
            components=components,
            relationships=relationships,
        )
