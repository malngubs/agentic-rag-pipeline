/**
 * ============================================================================
 * ❓ HELP & SUPPORT PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Help center with getting started guides, feature documentation,
 * FAQs, and support contact information.
 */

'use client';

import React, { useState } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HelpCircle,
  Book,
  MessageSquare,
  FileText,
  BarChart3,
  Upload,
  Search,
  Sparkles,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Mail,
  Github,
  Lightbulb,
  Zap,
  Shield,
  Database,
  Settings,
  Palette,
  Play,
} from 'lucide-react';

// =============================================================================
// GETTING STARTED STEPS
// =============================================================================

const gettingStartedSteps = [
  {
    step: 1,
    title: 'Upload Your Data',
    description: 'Start by uploading your documents (CSV, Excel, PDF, etc.) to build your knowledge base.',
    icon: Upload,
    action: '/documents',
    actionLabel: 'Go to Documents',
  },
  {
    step: 2,
    title: 'Ask Questions',
    description: 'Use natural language to ask questions about your data. The AI will search your knowledge base and provide intelligent answers.',
    icon: MessageSquare,
    action: '/chat',
    actionLabel: 'Start Chatting',
  },
  {
    step: 3,
    title: 'Create Dashboards',
    description: 'Build visual dashboards with charts and KPIs to track your key metrics.',
    icon: BarChart3,
    action: '/dashboards',
    actionLabel: 'Create Dashboard',
  },
  {
    step: 4,
    title: 'Customize Your Experience',
    description: 'Personalize the platform with theme colors and configure your preferences.',
    icon: Settings,
    action: '/settings',
    actionLabel: 'Open Settings',
  },
];

// =============================================================================
// FEATURES
// =============================================================================

const features = [
  {
    icon: Sparkles,
    title: 'AI-Powered Chat',
    description: 'Ask questions in natural language and get intelligent answers based on your uploaded documents. The RAG (Retrieval-Augmented Generation) system ensures accurate, contextual responses.',
  },
  {
    icon: Database,
    title: 'Knowledge Base',
    description: 'Upload and manage documents that form your searchable knowledge base. Supports CSV, Excel, PDF, JSON, and text files.',
  },
  {
    icon: BarChart3,
    title: 'Interactive Dashboards',
    description: 'Create beautiful dashboards with charts, tables, and KPIs. Visualize your data and track important metrics.',
  },
  {
    icon: Zap,
    title: 'Real-time Streaming',
    description: 'Get instant responses with WebSocket streaming. Watch answers appear in real-time as they are generated.',
  },
  {
    icon: Shield,
    title: 'Source Citations',
    description: 'Every AI response includes citations to the source documents, ensuring transparency and traceability.',
  },
  {
    icon: Palette,
    title: 'Theme Customization',
    description: 'Choose from 8 beautiful color themes to personalize your experience. Theme preferences sync across all devices.',
  },
];

// =============================================================================
// FAQ ITEMS
// =============================================================================

const faqItems = [
  {
    question: 'What file types can I upload?',
    answer: 'The platform supports CSV, Excel (.xlsx, .xls), JSON, PDF, TXT, DOC, DOCX, and Markdown files. Each file is processed and chunked for optimal retrieval.',
  },
  {
    question: 'How does the AI find answers from my documents?',
    answer: 'We use RAG (Retrieval-Augmented Generation) technology. When you ask a question, the system searches your uploaded documents using semantic similarity, retrieves the most relevant chunks, and uses an LLM to generate an accurate answer based on that context.',
  },
  {
    question: 'Is my data secure?',
    answer: 'Yes, your data is stored locally on the server you configure. Documents are processed and stored in a vector database for efficient retrieval. No data is sent to external services except for the AI inference calls.',
  },
  {
    question: 'What AI models are used?',
    answer: 'The platform uses GPT-4o-mini by default for fast, cost-effective responses. The model can be configured in the backend settings to use other OpenAI models or compatible alternatives.',
  },
  {
    question: 'Can I create visualizations from my data?',
    answer: 'Yes! You can ask the AI to create charts, tables, and dashboards. Try prompts like "Create a bar chart showing sales by region" or "Build a dashboard with key metrics".',
  },
  {
    question: 'How do I delete uploaded documents?',
    answer: 'Go to the Documents page, find the document you want to remove, click the menu icon (three dots), and select "Delete". The document will be removed from the knowledge base.',
  },
  {
    question: 'Can multiple users access the platform?',
    answer: 'Yes, the platform supports multi-tenant architecture. Each user can have their own session and document scope. User management features are available in the admin panel.',
  },
  {
    question: 'How do I customize the theme?',
    answer: 'Click on "Theme Color" in the sidebar or go to Settings > Theme & Appearance. Choose from 8 preset color themes - your preference will sync across all your sessions.',
  },
];

// =============================================================================
// FAQ ITEM COMPONENT
// =============================================================================

interface FAQItemProps {
  question: string;
  answer: string;
  isOpen: boolean;
  onToggle: () => void;
}

const FAQItem: React.FC<FAQItemProps> = ({ question, answer, isOpen, onToggle }) => (
  <div className="border border-border rounded-xl overflow-hidden">
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-4 text-left hover:bg-surface-hover transition-colors"
    >
      <span className="font-medium text-foreground pr-4">{question}</span>
      <ChevronDown
        className={`w-5 h-5 text-foreground-muted flex-shrink-0 transition-transform ${
          isOpen ? 'rotate-180' : ''
        }`}
      />
    </button>
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-hidden"
        >
          <div className="px-4 pb-4 text-foreground-secondary">{answer}</div>
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);

// =============================================================================
// SECTION HEADER COMPONENT
// =============================================================================

interface SectionHeaderProps {
  icon: React.ElementType;
  title: string;
  description?: string;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ icon: Icon, title, description }) => (
  <div className="flex items-start gap-4 mb-6">
    <div className="w-12 h-12 rounded-xl bg-brand-600/10 flex items-center justify-center flex-shrink-0">
      <Icon className="w-6 h-6 text-brand-500" />
    </div>
    <div>
      <h2 className="text-xl font-semibold text-foreground">{title}</h2>
      {description && <p className="text-foreground-muted mt-1">{description}</p>}
    </div>
  </div>
);

// =============================================================================
// MAIN HELP PAGE
// =============================================================================

export default function HelpPage() {
  const [openFAQ, setOpenFAQ] = useState<number | null>(null);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-background">
        <div className="max-w-4xl mx-auto p-8">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="w-20 h-20 rounded-2xl bg-brand-600/10 flex items-center justify-center mx-auto mb-6">
              <HelpCircle className="w-10 h-10 text-brand-500" />
            </div>
            <h1 className="text-3xl font-bold text-foreground mb-3">Help & Support</h1>
            <p className="text-lg text-foreground-secondary max-w-2xl mx-auto">
              Welcome to Macrocomm BI! Learn how to get the most out of the platform
              with our guides and documentation.
            </p>
          </div>

          {/* Getting Started */}
          <section className="mb-12">
            <SectionHeader
              icon={Play}
              title="Getting Started"
              description="Follow these steps to start using the platform"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {gettingStartedSteps.map((step) => (
                <motion.div
                  key={step.step}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: step.step * 0.1 }}
                  className="group relative bg-surface rounded-xl border border-border p-5 hover:border-brand-500/50 hover:shadow-lg transition-all"
                >
                  {/* Step number */}
                  <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white font-bold text-sm">
                    {step.step}
                  </div>

                  <div className="flex items-start gap-4 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center flex-shrink-0">
                      <step.icon className="w-5 h-5 text-brand-500" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground mb-1">{step.title}</h3>
                      <p className="text-sm text-foreground-muted">{step.description}</p>
                    </div>
                  </div>

                  <a
                    href={step.action}
                    className="flex items-center gap-2 text-sm text-brand-500 hover:text-brand-400 font-medium transition-colors"
                  >
                    {step.actionLabel}
                    <ChevronRight className="w-4 h-4" />
                  </a>
                </motion.div>
              ))}
            </div>
          </section>

          {/* Features */}
          <section className="mb-12">
            <SectionHeader
              icon={Lightbulb}
              title="Platform Features"
              description="Discover what you can do with Macrocomm BI"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-surface rounded-xl border border-border p-5"
                >
                  <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center mb-4">
                    <feature.icon className="w-5 h-5 text-brand-500" />
                  </div>
                  <h3 className="font-semibold text-foreground mb-2">{feature.title}</h3>
                  <p className="text-sm text-foreground-muted">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </section>

          {/* FAQ */}
          <section className="mb-12">
            <SectionHeader
              icon={Book}
              title="Frequently Asked Questions"
              description="Find answers to common questions"
            />
            <div className="space-y-3">
              {faqItems.map((item, index) => (
                <FAQItem
                  key={index}
                  question={item.question}
                  answer={item.answer}
                  isOpen={openFAQ === index}
                  onToggle={() => setOpenFAQ(openFAQ === index ? null : index)}
                />
              ))}
            </div>
          </section>

          {/* Tips & Tricks */}
          <section className="mb-12">
            <SectionHeader
              icon={Zap}
              title="Tips & Tricks"
              description="Get more out of your experience"
            />
            <div className="bg-gradient-to-br from-brand-600/10 to-brand-500/5 rounded-xl border border-brand-500/20 p-6">
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-brand-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-brand-500 font-bold text-xs">1</span>
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Be specific with your questions</p>
                    <p className="text-sm text-foreground-muted">
                      Instead of &ldquo;show data&rdquo;, try &ldquo;show me the total sales by product category for Q4 2024&rdquo;
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-brand-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-brand-500 font-bold text-xs">2</span>
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Use keyboard shortcuts</p>
                    <p className="text-sm text-foreground-muted">
                      Press <kbd className="px-2 py-0.5 bg-surface border border-border rounded text-xs">Enter</kbd> to send messages, <kbd className="px-2 py-0.5 bg-surface border border-border rounded text-xs">Shift + Enter</kbd> for new lines
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-brand-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-brand-500 font-bold text-xs">3</span>
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Drag and drop files</p>
                    <p className="text-sm text-foreground-muted">
                      You can drag files directly into the chat or upload area - no need to click the file picker
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-brand-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-brand-500 font-bold text-xs">4</span>
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Check source citations</p>
                    <p className="text-sm text-foreground-muted">
                      Click on the sources section in AI responses to see exactly which documents were used
                    </p>
                  </div>
                </li>
              </ul>
            </div>
          </section>

          {/* Contact Support */}
          <section>
            <SectionHeader
              icon={Mail}
              title="Need More Help?"
              description="Get in touch with our support team"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <a
                href="mailto:support@macrocomm.ai"
                className="flex items-center gap-4 p-5 bg-surface rounded-xl border border-border hover:border-brand-500/50 hover:shadow-lg transition-all group"
              >
                <div className="w-12 h-12 rounded-xl bg-brand-600/10 flex items-center justify-center">
                  <Mail className="w-6 h-6 text-brand-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground group-hover:text-brand-500 transition-colors">
                    Email Support
                  </h3>
                  <p className="text-sm text-foreground-muted">support@macrocomm.ai</p>
                </div>
                <ExternalLink className="w-4 h-4 text-foreground-muted ml-auto" />
              </a>

              <a
                href="https://github.com/macrocomm/bi-platform"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-4 p-5 bg-surface rounded-xl border border-border hover:border-brand-500/50 hover:shadow-lg transition-all group"
              >
                <div className="w-12 h-12 rounded-xl bg-brand-600/10 flex items-center justify-center">
                  <Github className="w-6 h-6 text-brand-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground group-hover:text-brand-500 transition-colors">
                    GitHub Repository
                  </h3>
                  <p className="text-sm text-foreground-muted">Report issues & contribute</p>
                </div>
                <ExternalLink className="w-4 h-4 text-foreground-muted ml-auto" />
              </a>
            </div>
          </section>

          {/* Footer */}
          <div className="mt-12 pt-8 border-t border-border text-center">
            <p className="text-sm text-foreground-muted">
              Macrocomm BI Platform &mdash; Built with AI for intelligent business insights
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
