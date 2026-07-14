import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { chatApi } from '@/api/chatApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ArrowLeft, Send, Trash2, Bot, User } from 'lucide-react';

export default function Chat() {
  const { contractId } = useParams();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const loadHistory = async () => {
    try {
      const data = await chatApi.getHistory(contractId);
      // Sort messages by created_at assuming the backend returns them unordered or oldest first.
      // Usually it's oldest first for chat history display.
      const sorted = (data.messages || []).sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      setMessages(sorted);
    } catch (err) {
      console.error("Failed to load chat history", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [contractId]);

  useEffect(() => {
    // Scroll to bottom whenever messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const userMessage = { role: 'user', content: input, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setSending(true);

    try {
      const res = await chatApi.sendMessage(contractId, userMessage.content);
      const assistantMessage = { 
        role: 'assistant', 
        content: res.answer, 
        citations: res.citations,
        created_at: new Date().toISOString() 
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      alert("Failed to send message. Please try again.");
      // Optionally remove the optimistically added user message here
    } finally {
      setSending(false);
    }
  };

  const handleClear = async () => {
    if (!window.confirm("Are you sure you want to clear the chat history?")) return;
    try {
      await chatApi.clearHistory(contractId);
      setMessages([]);
    } catch (err) {
      alert("Failed to clear history.");
    }
  };

  if (loading) return <div className="flex items-center justify-center h-full">Loading...</div>;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] gap-4">
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" className="-ml-4" asChild>
          <Link to={`/contracts/${contractId}`}><ArrowLeft className="mr-2 h-4 w-4" /> Back to Contract</Link>
        </Button>
        <Button variant="ghost" size="sm" onClick={handleClear} disabled={messages.length === 0}>
          <Trash2 className="mr-2 h-4 w-4" /> Clear History
        </Button>
      </div>

      <Card className="flex flex-col flex-1 overflow-hidden bg-background">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
              Start a conversation about this contract.
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                    <Bot className="h-5 w-5 text-primary-foreground" />
                  </div>
                )}
                <div className={`max-w-[80%] rounded-lg p-4 ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                  <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                  
                  {/* Citations block */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border/50 text-xs text-muted-foreground space-y-1">
                      <span className="font-semibold block mb-1">Sources:</span>
                      {msg.citations.map((cit, i) => (
                        <div key={i} className="bg-background/50 p-2 rounded truncate" title={cit.text_snippet}>
                          [Page {cit.page_number || 'N/A'}] ...{cit.text_snippet.substring(0, 80)}...
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
                    <User className="h-5 w-5 text-secondary-foreground" />
                  </div>
                )}
              </div>
            ))
          )}
          {sending && (
            <div className="flex gap-4">
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                <Bot className="h-5 w-5 text-primary-foreground" />
              </div>
              <div className="max-w-[80%] rounded-lg p-4 bg-muted animate-pulse flex space-x-2">
                <div className="h-2 w-2 bg-primary/50 rounded-full"></div>
                <div className="h-2 w-2 bg-primary/50 rounded-full animation-delay-200"></div>
                <div className="h-2 w-2 bg-primary/50 rounded-full animation-delay-400"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 bg-muted/20 border-t">
          <form onSubmit={handleSend} className="flex gap-2">
            <Input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about the contract..."
              className="flex-1 bg-background"
              disabled={sending}
            />
            <Button type="submit" disabled={!input.trim() || sending}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
