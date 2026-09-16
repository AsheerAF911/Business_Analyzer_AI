# LLM Provider Layer

## Purpose

The Business AI application uses an external LLM to generate
answers from evidence retrieved by the RAG pipeline.

The provider layer prevents business and RAG logic from
depending directly on a particular LLM provider or SDK.

This change is an architectural abstraction only.

It does not modify retrieval, embeddings, Qdrant, chunking,
or the application's API contract.

---

## Previous Architecture

Previously the application used:

Question
↓
RetrievalService
↓
Retrieved Evidence
↓
AnswerService
↓
OpenRouter-backed LLM implementation
↓
Answer

The existing LLM abstraction combined the concepts of an
application LLM service and a provider implementation.

---

## New Architecture

Question
↓
RetrievalService
↓
Retrieved Evidence
↓
AnswerService
↓
LLMService
↓
LLMProvider
↓
OpenRouterProvider
↓
OpenRouter API

The rest of the application depends on LLMService.

Provider-specific behavior exists below the LLMProvider
boundary.

---

## LLMService Responsibility

LLMService is an application-level service.

It accepts:

- a user question
- retrieved evidence
- application instructions

It converts these inputs into an LLMRequest and delegates
generation to the configured LLMProvider.

LLMService does not know about OpenRouter, the OpenAI SDK,
provider URLs, provider authentication, or provider-specific
response objects.

---

## LLMProvider Responsibility

LLMProvider defines the capability required from an LLM
provider.

A provider must accept an application-level LLMRequest and
return an application-level LLMResponse.

Provider implementations are responsible for translating
between these application models and provider-specific SDK
formats.

---

## Current Provider

The current provider is OpenRouterProvider.

It contains:

- OpenRouter API configuration
- API authentication
- model configuration
- OpenAI-compatible SDK initialization
- provider request construction
- provider response parsing
- provider-specific errors

The provider continues using the same current OpenRouter
configuration.

No second provider was introduced.

---

## Application Boundary

Business intelligence and RAG components must never import
or use the provider SDK directly.

Allowed:

BusinessInvestigationService
↓
LLMService
↓
LLMProvider
↓
Provider SDK

Not allowed:

BusinessInvestigationService
↓
OpenAI/OpenRouter SDK

The frontend also remains provider-independent.

---

## Security and Privacy

The provider abstraction does not make the application
private.

Retrieved business evidence passed to LLMService may still
be transmitted to the currently configured external
provider.

The abstraction only establishes a boundary that allows the
provider to be replaced later.

A production deployment may eventually use:

- an approved enterprise AI provider
- a private model deployment
- a self-hosted/local LLM

Provider selection must still account for data governance,
security, privacy, and contractual requirements.

---

## Future Provider

A future provider could implement the same LLMProvider
contract:

                LLMService
                     |
        +------------+------------+
        |            |            |
        v            v            v
   Cloud        Enterprise      Local
  Provider       Provider        LLM

For example, a future LocalLLMProvider would implement:

LLMProvider.generate(LLMRequest) -> LLMResponse

The rest of the application would remain unchanged:

- RetrievalService
- BGE-M3
- Qdrant
- chunking
- AnswerService
- /api/ask
- React frontend

Only provider construction/configuration would change.

---

## Intentionally Not Added

This provider layer does not introduce:

- multiple active providers
- provider fallback
- model routing
- agents
- function calling
- local models
- LangChain
- plugin architecture
- microservices
- message queues

The goal is a small provider-independent architectural
boundary suitable for the current MVP.