"use client";
import { useState } from 'react';
import { z } from 'zod';
import { useAgentRunner } from '../../../../../hooks/useAgentRunner.ts';

const msgSchema = z.string().trim().min(1);
interface Message { role: 'user' | 'assistant'; text: string }

export default function AgentChat() {
  const { run } = useAgentRunner();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const prompt = msgSchema.parse(input);
      setMessages(m => [...m, { role: 'user', text: prompt }, { role: 'assistant', text: '' }]);
      await run(prompt, { onChunk: (chunk) => setMessages(m => { const u = [...m]; u[u.length - 1].text += chunk; return u; }) });
      setInput('');
    } catch (err) { console.error(err); }
  };
  return (
    <div>
      <ul role="log" aria-live="polite" aria-relevant="additions" className="mb-2 space-y-2">{messages.map((m, i) => (<li key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>{m.text}</li>))}</ul>
      <form onSubmit={handleSend} className="flex gap-2">
        <label htmlFor="message" className="sr-only">Message</label>
        <input id="message" value={input} onChange={e => setInput(e.target.value)} className="flex-1 border p-2" />
        <button type="submit" aria-label="Send message" className="px-4 py-2 bg-blue-500 text-white">Send</button>
      </form>
    </div>
  );
}
