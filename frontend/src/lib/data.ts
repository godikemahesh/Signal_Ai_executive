export interface Signal {
  id: string;
  subject: string;
  sender: string;
  senderEmail: string;
  preview: string;
  category: 'interview' | 'finance' | 'shopping' | 'personal' | 'github' | 'newsletter' | 'marketing';
  bucket: 'do-now' | 'today' | 'this-week' | 'waiting' | 'completed' | 'ignored';
  status: 'new' | 'changed' | 'stable';
  priority: number; // internal 0-100, not shown to user
  actionType: 'reply' | 'pay' | 'upload' | 'complete' | 'review' | 'no-action';
  deadline?: string; // ISO date
  deadlineText?: string; // human readable like "Due today at 6 PM"
  entityName: string; // e.g. "Google SWE Internship"
  entityType: 'interview' | 'order' | 'bill' | 'subscription' | 'general';
  gmailUrl: string;
  createdAt: string;
  updatedAt: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  subject: string;
  summary: string;
}

export interface Entity {
  id: string;
  name: string;
  type: 'interview' | 'order' | 'bill' | 'subscription' | 'general';
  category?: 'all' | 'interview' | 'order' | 'general';
  lastUpdated: string;
  events: TimelineEvent[];
}

export interface BehaviorInsight {
  id: string;
  category: string;
  pattern: string;
  confidence: number; // 0-100
  impact: string;
  actionTaken: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export const initialSignals: Signal[] = [
  {
    id: '1',
    subject: 'Reply to Stripe recruiter',
    sender: 'Sarah Chen',
    senderEmail: 'sarah@stripe.com',
    preview: 'Hi Mahesh, thanks for your interest! Can you share your availability for next week? We have slots on Tuesday 2 PM, Wednesday 10 AM, and Thursday 3 PM.',
    category: 'interview',
    bucket: 'do-now',
    status: 'new',
    priority: 96,
    actionType: 'reply',
    deadlineText: 'Fast responder — reply expected today',
    entityName: 'Stripe — Backend Engineer',
    entityType: 'interview',
    gmailUrl: 'https://mail.google.com/mail/u/0/#inbox/abc123',
    createdAt: '2026-08-10T10:30:00Z',
    updatedAt: '2026-08-10T10:30:00Z',
  },
  {
    id: '2',
    subject: 'Complete your HackerRank assessment',
    sender: 'Google Recruiting',
    senderEmail: 'recruiting@google.com',
    preview: 'Your online assessment is ready. You have 90 minutes to complete 2 algorithmic problems. Deadline: August 10, 6:00 PM IST.',
    category: 'interview',
    bucket: 'do-now',
    status: 'changed',
    priority: 94,
    actionType: 'complete',
    deadline: '2026-08-10T18:00:00Z',
    deadlineText: 'Due today at 6:00 PM',
    entityName: 'Google — SWE Internship',
    entityType: 'interview',
    gmailUrl: 'https://mail.google.com/mail/u/0/#inbox/def456',
    createdAt: '2026-08-08T14:00:00Z',
    updatedAt: '2026-08-10T08:00:00Z',
  },
  {
    id: '3',
    subject: 'Your Amazon order has shipped',
    sender: 'Amazon.in',
    senderEmail: 'shipment-tracking@amazon.in',
    preview: 'Your order #403-9283715-9283715 (Keychron K2 Mechanical Keyboard) is out for delivery. Expected delivery: Today by 8 PM.',
    category: 'shopping',
    bucket: 'today',
    status: 'changed',
    priority: 65,
    actionType: 'no-action',
    deadlineText: 'Out for delivery — expected today',
    entityName: 'Amazon Order — Mechanical Keyboard',
    entityType: 'order',
    gmailUrl: 'https://mail.google.com/mail/u/0/#inbox/ghi789',
    createdAt: '2026-08-05T06:00:00Z',
    updatedAt: '2026-08-10T07:30:00Z',
  },
  {
    id: '4',
    subject: 'Electricity Bill — Final Reminder',
    sender: 'BESCOM',
    senderEmail: 'noreply@bescom.co.in',
    preview: 'Your electricity bill for August 2026 is ₹2,140. Due date: August 11, 2026. Pay now to avoid late charges.',
    category: 'finance',
    bucket: 'today',
    status: 'stable',
    priority: 78,
    actionType: 'pay',
    deadline: '2026-08-11T23:59:00Z',
    deadlineText: 'Due tomorrow',
    entityName: 'Electricity Bill — BESCOM',
    entityType: 'bill',
    gmailUrl: 'https://mail.google.com/mail/u/0/#inbox/jkl012',
    createdAt: '2026-08-01T00:00:00Z',
    updatedAt: '2026-08-09T00:00:00Z',
  },
  {
    id: '5',
    subject: 'Scholarship Document Submission',
    sender: 'IIT Madras',
    senderEmail: 'scholarships@iitm.ac.in',
    preview: 'Please upload your income certificate and bank account details before August 13, 2026 to complete your scholarship application.',
    category: 'personal',
    bucket: 'this-week',
    status: 'stable',
    priority: 82,
    actionType: 'upload',
    deadline: '2026-08-13T23:59:00Z',
    deadlineText: 'Due in 3 days',
    entityName: 'IIT Madras Scholarship',
    entityType: 'general',
    gmailUrl: 'https://mail.google.com/mail/u/0/#inbox/mno345',
    createdAt: '2026-08-07T09:00:00Z',
    updatedAt: '2026-08-07T09:00:00Z',
  },
  {
    id: '6',
    subject: 'Re: Project discussion',
    sender: 'Rahul Sharma',
    senderEmail: 'rahul.sharma@gmail.com',
    preview: 'Hey man, sorry for the late reply. Been 3 weeks! Yeah I am free this weekend, let us catch up. Saturday evening works?',
    category: 'personal',
    bucket: 'today',
    status: 'new',
    priority: 60,
    actionType: 'reply',
    deadlineText: 'Replied after 3 weeks',
    entityName: 'Rahul Sharma',
    entityType: 'general',
    gmailUrl: 'https://mail.google.com/mail/u/0/#inbox/pqr678',
    createdAt: '2026-08-10T09:00:00Z',
    updatedAt: '2026-08-10T09:00:00Z',
  },
  {
    id: '7',
    subject: 'CI failed on CareerOS repo',
    sender: 'GitHub',
    senderEmail: 'noreply@github.com',
    preview: 'Build #142 failed. Error in test suite. Not blocking deployment. Check logs for details.',
    category: 'github',
    bucket: 'this-week',
    status: 'stable',
    priority: 45,
    actionType: 'review',
    deadlineText: 'Non-blocking',
    entityName: 'CareerOS Repository',
    entityType: 'general',
    gmailUrl: 'https://mail.google.com/mail/u/0/#inbox/stu901',
    createdAt: '2026-08-10T05:00:00Z',
    updatedAt: '2026-08-10T05:00:00Z',
  },
  {
    id: '8',
    subject: '20% off JetBrains annual subscription',
    sender: 'JetBrains',
    senderEmail: 'marketing@jetbrains.com',
    preview: 'Get 20% off your annual subscription. Limited time offer!',
    category: 'marketing',
    bucket: 'ignored',
    status: 'stable',
    priority: 12,
    actionType: 'no-action',
    deadlineText: 'Auto-archived',
    entityName: 'JetBrains Offer',
    entityType: 'subscription',
    gmailUrl: 'https://mail.google.com/mail/u/0/#inbox/vwx234',
    createdAt: '2026-08-10T04:00:00Z',
    updatedAt: '2026-08-10T04:00:00Z',
  },
];

export const mockSignals = initialSignals;

export const mockEntities: Entity[] = [
  {
    id: 'e1',
    name: 'Google SWE Internship',
    type: 'interview',
    category: 'interview',
    lastUpdated: '10 min ago',
    events: [
      { id: 'ev1', timestamp: 'Aug 3', subject: 'Application submitted', summary: 'Applied via careers.google.com' },
      { id: 'ev2', timestamp: 'Aug 5', subject: 'Resume shortlisted', summary: 'Recruiter reached out for next steps' },
      { id: 'ev3', timestamp: 'Aug 8', subject: 'OA link sent', summary: 'HackerRank assessment — due today 6 PM' },
    ],
  },
  {
    id: 'e2',
    name: 'Amazon Order — Mechanical Keyboard',
    type: 'order',
    category: 'order',
    lastUpdated: '1 hr ago',
    events: [
      { id: 'ev4', timestamp: 'Aug 5', subject: 'Order confirmed', summary: 'Keychron K2 — ₹8,499' },
      { id: 'ev5', timestamp: 'Aug 6', subject: 'Shipped', summary: 'Dispatched from Bangalore warehouse' },
      { id: 'ev6', timestamp: 'Aug 9', subject: 'Out for delivery', summary: 'Expected today by 8 PM' },
    ],
  },
  {
    id: 'e3',
    name: 'Electricity Bill — BESCOM',
    type: 'bill',
    category: 'general',
    lastUpdated: '1 day ago',
    events: [
      { id: 'ev7', timestamp: 'Aug 1', subject: 'Bill generated', summary: '₹2,140 for July 2026' },
      { id: 'ev8', timestamp: 'Aug 7', subject: 'First reminder', summary: 'Payment due in 4 days' },
      { id: 'ev9', timestamp: 'Aug 9', subject: 'Final reminder', summary: 'Due tomorrow — pay now' },
    ],
  },
];

export const mockBehaviorInsights: BehaviorInsight[] = [
  { id: 'b1', category: 'Interview signals', pattern: 'Open within 3 minutes', confidence: 96, impact: '+96% priority', actionTaken: 'Auto-prioritize to top' },
  { id: 'b2', category: 'Manager emails', pattern: 'Reply within 10 minutes', confidence: 92, impact: 'Flagged urgent', actionTaken: 'Flag as urgent' },
  { id: 'b3', category: 'GitHub notifications', pattern: 'Open within 1 hour', confidence: 78, impact: 'Shifted bucket', actionTaken: 'Sort to Today bucket' },
  { id: 'b4', category: 'Electricity bills', pattern: 'Pay on the last day', confidence: 85, impact: 'Filtered noise', actionTaken: 'Flag as Due Soon, not Do Now' },
  { id: 'b5', category: 'Flipkart offers', pattern: 'Ignored 27/27 times', confidence: 98, impact: 'Zero interruption', actionTaken: 'Auto-archive' },
  { id: 'b6', category: 'LinkedIn newsletters', pattern: 'Never read', confidence: 99, impact: 'AI Digest', actionTaken: 'Auto-summarize' },
];

export const mockChatHistory: ChatMessage[] = [
  { id: 'c1', role: 'assistant', content: "I am tracking 147 signals from your life. What would you like to know?", timestamp: '2026-08-10T08:00:00Z' },
];

export const suggestedPrompts = [
  { id: 'p1', text: "Which companies rejected me this month?" },
  { id: 'p2', text: "What needs my attention right now?" },
  { id: 'p3', text: "Show all interview invitations" },
  { id: 'p4', text: "Any deadlines this week?" },
  { id: 'p5', text: "Applications with no reply >10 days" },
];

export const quickPrompts = suggestedPrompts.map(p => p.text);

export const promptResponses: Record<string, string> = {
  "Which companies rejected me this month?": `This month, 3 companies sent rejection signals:

1. Meta — Aug 2 (Applied: Jul 15, Rejected after resume screen)
2. Microsoft — Aug 6 (Applied: Jul 20, Rejected after OA)
3. Atlassian — Aug 8 (Applied: Jul 28, Rejected after technical round)

I've archived all three and logged them to your tracker.`,

  "What needs my attention right now?": `3 things need your attention right now:

1. Reply to Stripe recruiter
They asked for interview slots. You typically reply within 30 minutes.

2. Complete Google assessment
Due at 6:00 PM today. Final round before onsite.

3. Pay electricity bill
₹2,140 due tomorrow. You usually pay on the last day.`,

  "Show all interview invitations": `You have 2 active interview pipelines and 1 upcoming interview:

Active:
• Google — OA due today (Aug 10)
• Stripe — Scheduling in progress (replied Aug 9)

Upcoming:
• Amazon — SDE Intern, scheduled Aug 14 at 2:00 PM
  (Zoom link extracted and added to calendar)`,

  "Any deadlines this week?": `2 deadlines this week:

Aug 10 (Today) — Google HackerRank assessment
Aug 13 (Thu) — IIT Madras scholarship documents

Plus 1 subscription renewal on Aug 15 (Vercel Pro — $20).`,

  "Applications with no reply >10 days": `5 applications with no response for 10+ days:

• Netflix — Applied Jul 25 (16 days ago)
• Airbnb — Applied Jul 27 (14 days ago)
• Uber — Applied Jul 28 (13 days ago)
• Coinbase — Applied Jul 30 (11 days ago)
• Notion — Applied Jul 30 (11 days ago)

Would you like me to draft follow-up messages?`,
};
