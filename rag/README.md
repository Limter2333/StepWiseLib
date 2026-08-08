1. 安装依赖

```commandline
uv add sentence_transformers chromadb google-genai python-dotenv
```

2. 运行 jupyter

```commandline
uv run --with jupyter jupyter lab
```

3. 安装依赖

将缺失的依赖添加到 pyproject.toml，运行后安装

```commandline
uv sync
```
