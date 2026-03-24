# Privacy and Data Handling

This document explains how SmartFlow AI handles user data in the current codebase. It is meant to be practical and readable, not a long legal policy.

The bot accepts:

- text messages;
- voice messages;
- uploaded documents (`PDF`, `DOCX`, `TXT`).

## What is stored

### 1. Conversation history in Redis

SmartFlow AI stores chat memory in Redis on a per-`user_id + chat_id` basis.

What is stored there:

- user text messages;
- assistant text replies;
- transcribed text from voice messages;
- assistant replies generated after voice interactions.

What is not stored there:

- raw voice audio files;
- retrieved RAG context as part of long-term memory.

By default, this memory is temporary:

- it is limited to the latest `MAX_HISTORY` exchanges;
- it expires automatically after `MEMORY_TTL` seconds.

In the default configuration, that means up to `15` exchanges with a `24h` TTL, but both values are configurable.

### 2. Documents and vector data in Qdrant

When a user uploads a document, the bot downloads it, extracts text, splits it into chunks, creates embeddings, and stores the indexed chunks in Qdrant.

What is stored in Qdrant:

- document chunks used for retrieval;
- vector embeddings for those chunks;
- metadata used to scope retrieval and deletion, including `user_id`, `chat_id`, `source_id`, `source_name`, and Telegram file identifiers (`telegram_file_id`, `telegram_file_unique_id`).

This data is scoped to the current user and chat, so retrieval is filtered by `user_id + chat_id`.

### 3. Temporary local files in `DATA_DIR`

The bot also uses a local working directory for temporary processing.

Examples:

- uploaded documents before parsing and indexing;
- downloaded voice messages in `.ogg`;
- converted audio in `.wav`;
- generated TTS replies in `.mp3`.

These files are intended to be temporary and are deleted after processing in the normal application flow.

## Where data is stored

In the default setup, data is stored in three places:

- `REDIS_URL`: temporary conversation history in Redis;
- `QDRANT_URL`: indexed document chunks, embeddings, and metadata in Qdrant;
- `DATA_DIR`: temporary local processing files on the application server.

If you self-host this project, the actual physical storage location depends on where your Redis instance, Qdrant instance, and application server are deployed.

## How data is used

User data is used only to make the bot work:

- to answer chat messages;
- to transcribe voice input;
- to retrieve relevant document context;
- to generate answers;
- to synthesize voice replies when voice output is enabled.

This codebase is not designed as a hidden analytics pipeline, a marketing database, or a general-purpose file vault.

## External model and speech providers

Some features rely on external AI or speech providers configured by the operator:

- chat responses are generated through the provider selected in `LLM_MODEL` via LiteLLM;
- document embeddings are generated through Google Gemini embeddings in the current implementation;
- voice transcription uses `faster-whisper` inside the application process;
- voice reply synthesis uses `edge-tts`.

That means relevant text or document content may be sent to third-party providers when those features are used. Based on the current implementation, this can include the configured LLM provider, Google for embeddings, and the speech provider behind `edge-tts`. If you deploy this bot for real users, you should review the privacy and retention terms of the providers you configure.

## User control and deletion

Data deletion is treated as part of the user experience, not as an afterthought. The bot exposes clear commands so users can control what remains in the system.

### `/clear`

Deletes conversation memory for the current `user_id + chat_id` scope from Redis.

Use it when the user wants to reset the current dialogue context.

### `/clear_docs`

Deletes uploaded document chunks and related vector data for the current `user_id + chat_id` scope from Qdrant.

Use it when the user wants to remove indexed documents and the data derived from them.

### Temporary files

Temporary files in `DATA_DIR` are removed automatically after successful or failed processing in the normal flow. They are not meant to be kept as a permanent archive.

## What the developer does and does not do

This project is built to reduce unnecessary retention and give users explicit control.

The code does:

- scope document retrieval by user and chat;
- keep conversation memory temporary through TTL and bounded history;
- provide user-facing deletion commands;
- remove processing files after use;
- use stored data only for bot features.

The code does not:

- intentionally keep uploaded files as a permanent document repository on the app server;
- persist document retrieval context into long-term chat memory;
- include built-in features for selling, advertising on, or profiling users from their content.

Important operational note: whoever runs the infrastructure can still have technical access to Redis, Qdrant, logs, and local storage. Privacy in production therefore depends not only on the code, but also on deployment, access control, backups, and operational discipline.

## Sensitive data

This project is not intended for storing highly sensitive data without separate hardening and agreement.

Do not treat the default setup as a secure vault for:

- secrets or credentials;
- regulated personal data;
- confidential legal, medical, financial, or internal corporate records.

If you need that level of protection, you should add separate safeguards such as stricter access control, encryption, backup and retention rules, regional hosting choices, and provider review.

## User responsibility and content rights

Users are responsible for what they upload and submit.

By using document upload and voice/text features, the user is responsible for ensuring that:

- the content is lawful to process;
- they have the necessary rights, permissions, or authorization to upload it;
- the content does not violate copyright, confidentiality, privacy, or contractual obligations.

## Summary

In short:

- text, voice, and documents are accepted by the bot;
- conversation history is stored temporarily in Redis;
- uploaded document chunks and vector data are stored in Qdrant;
- temporary processing files live in `DATA_DIR` and are deleted after use;
- `/clear` removes chat memory;
- `/clear_docs` removes indexed documents and related vector data;
- the project is built for bot functionality, not for unrelated exploitation of user data;
- users remain responsible for the legality and rights status of the content they upload.
