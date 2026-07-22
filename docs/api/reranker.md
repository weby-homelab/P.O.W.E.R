# Reranker

## `RerankerManager`

Cross-Encoder reranker. The local Jina model
**`jinaai/jina-reranker-v2-base-multilingual`** is CC-BY-NC-4.0 and is not a
production default. It is loaded only when
`POWER_ALLOW_NONCOMMERCIAL_MODELS=1` is set for permitted non-commercial use.
Otherwise configure a licensed reranker; the code fails before downloading the
NC model.

`POWER_EMBED_PROVIDER=qwen3` selects `Qwen3-Reranker-0.6B-ONNX`; its license
and revision still require an independent release-policy decision.

### Constructor

```python
RerankerManager(model_name: str = "jinaai/jina-reranker-v2-base-multilingual")
```

- `model_name`: the cross-encoder to load when the license policy permits it.

### Methods

#### `rerank(query: str, documents: list[str]) -> list[float]`

Predict relevance scores for a list of document strings against a query.

- **Parameters**:
    - `query` (str): The search query.
    - `documents` (list of strings): The documents to evaluate.
- **Returns**: A list of floats representing the predicted relevance score for each document (higher score means more relevant).
