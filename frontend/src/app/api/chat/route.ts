import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json();

    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');
    const model = genAI.getGenerativeModel({ 
      model: 'gemini-3-flash-preview',
      systemInstruction: 'You are an expert AI powerlifting and bodybuilding coach named HenShack AI. Answer questions clearly, accurately, and motivationally. Keep your answers concise, practical, and highly focused on gym form, nutrition, or workout plans. If you are asked something unrelated to fitness, politely decline.'
    });

    // Google Generative AI requires history to strictly start with a 'user' message
    // Strip out the first hardcoded 'assistant' greeting if it exists in the history array
    let historyToFormat = messages.slice(0, -1);
    if (historyToFormat.length > 0 && historyToFormat[0].role !== 'user') {
      historyToFormat = historyToFormat.slice(1);
    }

    const formattedHistory = historyToFormat.map((m: any) => ({
      role: m.role === 'user' ? 'user' : 'model',
      parts: [{ text: m.content }]
    }));

    const chat = model.startChat({ history: formattedHistory });
    const result = await chat.sendMessageStream(messages[messages.length - 1].content);

    const stream = new ReadableStream({
        async start(controller) {
          for await (const chunk of result.stream) {
            const chunkText = chunk.text();
            controller.enqueue(new TextEncoder().encode(chunkText));
          }
          controller.close();
        },
      });

    return new Response(stream, {
        headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  } catch (error) {
    console.error('Chat API Error:', error);
    return new Response('Error connecting to AI Coach.', { status: 500 });
  }
}
