import React from 'react';
import { Link, Navigate } from 'react-router-dom';
import { AuthContext } from '../../context/AuthContext';
import { Shield, Search, FileText, MessageSquare, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/ui/button';

export default function Landing() {
  const { user, loading } = React.useContext(AuthContext);

  // If user is already logged in, redirect to dashboard
  if (!loading && user) {
    return <Navigate to="/dashboard" replace />;
  }

  const features = [
    {
      name: 'Clause Extraction',
      description: 'Automatically pull key legal clauses from 100-page contracts in seconds.',
      icon: FileText,
    },
    {
      name: 'Risk Detection',
      description: 'Identify hidden liabilities, missing clauses, and non-standard terms instantly.',
      icon: Shield,
    },
    {
      name: 'Chat with Contracts',
      description: 'Ask questions in plain English and get answers with exact source citations.',
      icon: MessageSquare,
    },
    {
      name: 'Semantic Search',
      description: 'Search across your entire contract portfolio using AI-powered meaning, not just keywords.',
      icon: Search,
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 selection:bg-indigo-100 selection:text-indigo-900">
      {/* Navigation */}
      <nav className="fixed w-full bg-white/80 backdrop-blur-md z-50 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-2">
              <div className="bg-indigo-600 p-1.5 rounded-lg">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-slate-900 tracking-tight">ClauseIQ</span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                Sign in
              </Link>
              <Link to="/register">
                <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all hover:shadow">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative pt-32 pb-20 sm:pt-40 sm:pb-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <h1 className="text-5xl md:text-7xl font-extrabold text-slate-900 tracking-tight mb-8">
            Contract Intelligence <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">
              Powered by AI.
            </span>
          </h1>
          <p className="mt-4 text-xl text-slate-600 max-w-2xl mx-auto mb-10 leading-relaxed">
            Turn static PDFs and Word documents into searchable, analyzable data. Extract obligations, detect risks, and chat with your legal documents instantly.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link to="/register">
              <Button className="h-12 px-8 text-lg bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 group">
                Start for free
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" className="h-12 px-8 text-lg rounded-full border-slate-300 text-slate-700 hover:bg-slate-100 transition-all">
                Sign in to Dashboard
              </Button>
            </Link>
          </div>
        </div>

        {/* Decorative Background Elements */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-100/50 rounded-full blur-3xl -z-10 opacity-50 pointer-events-none"></div>
      </div>

      {/* Features Section */}
      <div className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Everything you need to manage risk</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Our end-to-end platform handles the heavy lifting of contract review so you can focus on strategy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => (
              <div key={feature.name} className="relative p-6 bg-slate-50 rounded-2xl border border-slate-100 hover:border-indigo-100 hover:shadow-lg transition-all duration-300 group">
                <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{feature.name}</h3>
                <p className="text-slate-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Social Proof / Trust Section */}
      <div className="py-20 bg-slate-900 text-white text-center">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold mb-8">Stop reading hundreds of pages manually.</h2>
          <div className="flex flex-col sm:flex-row justify-center items-center gap-6 text-slate-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-indigo-400" />
              <span>Secure Local Vector Database</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-indigo-400" />
              <span>Enterprise-Grade Encryption</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-indigo-400" />
              <span>FastAPI & PostgreSQL Powered</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white py-12 border-t border-slate-200 text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-indigo-600" />
          <span className="text-lg font-bold text-slate-900 tracking-tight">ClauseIQ</span>
        </div>
        <p className="text-slate-500">© {new Date().getFullYear()} ClauseIQ. All rights reserved.</p>
      </footer>
    </div>
  );
}
