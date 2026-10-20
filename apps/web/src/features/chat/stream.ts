export type SafetyLevel = 'none' | 'elevated' | 'urgent';

export type ChatEvent =
  | { type: 'safety'; level: SafetyLevel }
  | { type: 'token'; text: string }
  | { type: 'crisis' }
  | { type: 'done'; filtered: boolean };

/** Parse one Server-Sent Events block ("event: x\ndata: {...}"). */
export function parseEvent(block: string): ChatEvent | null {
  let name = '';
  let data = '{}';
  for (const line of block.split('\n')) {
    if (line.startsWith('event: ')) name = line.slice(7).trim();
    else if (line.startsWith('data: ')) data = line.slice(6);
  }
  const payload = JSON.parse(data) as Record<string, unknown>;
  switch (name) {
    case 'safety':
      return { type: 'safety', level: payload.level as SafetyLevel };
    case 'token':
      return { type: 'token', text: String(payload.text) };
    case 'crisis':
      return { type: 'crisis' };
    case 'done':
      return { type: 'done', filtered: Boolean(payload.filtered) };
    default:
      return null;
  }
}

/** POST a message and yield events as they arrive. */
export async function* sendMessage(
  sessionId: string,
  content: string,
  history: { role: 'user' | 'assistant'; content: string }[],
): AsyncGenerator<ChatEvent> {
  const response = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, history }),
  });
  if (!response.ok || !response.body) throw new Error(`chat request failed: ${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split('\n\n');
    buffer = blocks.pop() ?? '';
    for (const block of blocks) {
      const event = block.trim() ? parseEvent(block) : null;
      if (event) yield event;
    }
  }
}
