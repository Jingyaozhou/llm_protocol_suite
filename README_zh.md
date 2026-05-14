# LLM Protocol Suite

LLM Protocol Suite 解决的是不同 agent 项目之间的数据定义漂移问题：每个项目都容易自己发明一套 message、tool call、runtime、usage、error 和 provider response 结构，最后导致跨项目复用、调试、审计和 provider 适配都变得很痛苦。

这个包提供一层小而明确的协议数据层，用 Pydantic v2 定义模型消息、多模态内容、工具调用、Runtime Envelope、Tool Execution Policy、usage、错误对象和 provider adapter。目标是让不同 agent 项目共享同一种结构化 LLM 数据语言，而不是直接依赖某个 provider SDK 或某个 agent framework 的内部格式。

它不是 agent 框架，不负责调用模型 API、执行工具、重试、审批或工作流编排。它只定义、校验和转换这些系统可以共同使用的数据结构。

## 安装

```bash
pip install -e ".[dev]"
```

## 示例

```python
from llm_protocol_suite import ModelMessage, ModelRequest, TextPart

request = ModelRequest(
    model="deepseek-chat",
    messages=[
        ModelMessage(role="user", content=[TextPart(text="Hello")]),
    ],
)

print(request.model_dump())
```

## OpenAI 映射

```python
from llm_protocol_suite import ModelMessage, ModelRequest, TextPart
from llm_protocol_suite.adapters.openai import to_openai_chat_request

request = ModelRequest(
    model="gpt-4.1-mini",
    messages=[ModelMessage(role="user", content=[TextPart(text="Hello")])],
)

payload = to_openai_chat_request(request)
```

## 非目标

v0.1 不调用 provider API，不执行工具，不运行重试逻辑，不管理审批，也不做 agent 编排。
