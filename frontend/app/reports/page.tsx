/**
 * ============================================================================
 * SCHEDULED REPORTS & ALERTS - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Automated insights delivery system:
 * - Create scheduled reports (daily, weekly, monthly)
 * - Set up threshold-based alerts
 * - Email and notification delivery
 * - Report templates and customization
 * - Alert history and management
 */

'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  Calendar,
  Mail,
  Clock,
  Plus,
  Trash2,
  Edit3,
  Play,
  Pause,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ChevronRight,
  Send,
  FileText,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Target,
  Zap,
  Users,
  Download,
  Eye,
  EyeOff,
  RefreshCw,
  Loader2,
  X,
  Filter,
  Search,
  MoreVertical,
  Copy,
  Archive,
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

type ReportFrequency = 'daily' | 'weekly' | 'monthly' | 'quarterly';
type AlertOperator = 'greater_than' | 'less_than' | 'equals' | 'change_by' | 'change_by_percent';
type AlertPriority = 'low' | 'medium' | 'high' | 'critical';
type DeliveryChannel = 'email' | 'slack' | 'teams' | 'webhook';

interface ScheduledReport {
  id: string;
  name: string;
  description: string;
  frequency: ReportFrequency;
  nextRun: Date;
  lastRun?: Date;
  recipients: string[];
  dashboardId?: string;
  metrics: string[];
  format: 'pdf' | 'excel' | 'html';
  isActive: boolean;
  createdAt: Date;
}

interface Alert {
  id: string;
  name: string;
  metric: string;
  operator: AlertOperator;
  threshold: number;
  priority: AlertPriority;
  channels: DeliveryChannel[];
  recipients: string[];
  isActive: boolean;
  lastTriggered?: Date;
  triggerCount: number;
  createdAt: Date;
}

interface AlertHistory {
  id: string;
  alertId: string;
  alertName: string;
  triggeredAt: Date;
  value: number;
  threshold: number;
  status: 'triggered' | 'resolved' | 'acknowledged';
  message: string;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const FREQUENCIES: { value: ReportFrequency; label: string; description: string }[] = [
  { value: 'daily', label: 'Daily', description: 'Every day at specified time' },
  { value: 'weekly', label: 'Weekly', description: 'Once per week' },
  { value: 'monthly', label: 'Monthly', description: 'Once per month' },
  { value: 'quarterly', label: 'Quarterly', description: 'Every 3 months' },
];

const OPERATORS: { value: AlertOperator; label: string; symbol: string }[] = [
  { value: 'greater_than', label: 'Greater than', symbol: '>' },
  { value: 'less_than', label: 'Less than', symbol: '<' },
  { value: 'equals', label: 'Equals', symbol: '=' },
  { value: 'change_by', label: 'Changes by', symbol: '±' },
  { value: 'change_by_percent', label: 'Changes by %', symbol: '±%' },
];

const PRIORITIES: { value: AlertPriority; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: 'text-blue-500 bg-blue-500/10' },
  { value: 'medium', label: 'Medium', color: 'text-amber-500 bg-amber-500/10' },
  { value: 'high', label: 'High', color: 'text-orange-500 bg-orange-500/10' },
  { value: 'critical', label: 'Critical', color: 'text-red-500 bg-red-500/10' },
];

const SAMPLE_METRICS = [
  'Total Revenue',
  'Monthly Sales',
  'Customer Count',
  'Average Order Value',
  'Conversion Rate',
  'Churn Rate',
  'Net Profit Margin',
  'Inventory Levels',
];

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

const ReportCard: React.FC<{
  report: ScheduledReport;
  onEdit: () => void;
  onDelete: () => void;
  onToggle: () => void;
  onRunNow: () => void;
}> = ({ report, onEdit, onDelete, onToggle, onRunNow }) => {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className={`bg-surface border rounded-xl p-4 transition-all ${
      report.isActive ? 'border-border' : 'border-border/50 opacity-60'
    }`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            report.isActive ? 'bg-brand-600/10' : 'bg-surface-muted'
          }`}>
            <FileText className={`w-5 h-5 ${report.isActive ? 'text-brand-500' : 'text-foreground-muted'}`} />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{report.name}</h3>
            <p className="text-xs text-foreground-muted">{report.description}</p>
          </div>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 hover:bg-surface-hover rounded"
          >
            <MoreVertical className="w-4 h-4 text-foreground-muted" />
          </button>
          {showMenu && (
            <div className="absolute right-0 top-full mt-1 w-40 bg-surface border border-border rounded-lg shadow-lg z-10">
              <button
                onClick={() => { onEdit(); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover"
              >
                <Edit3 className="w-4 h-4" /> Edit
              </button>
              <button
                onClick={() => { onRunNow(); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover"
              >
                <Play className="w-4 h-4" /> Run Now
              </button>
              <button
                onClick={() => { onToggle(); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover"
              >
                {report.isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {report.isActive ? 'Pause' : 'Resume'}
              </button>
              <button
                onClick={() => { onDelete(); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:bg-red-500/10"
              >
                <Trash2 className="w-4 h-4" /> Delete
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="p-2 bg-surface-muted rounded-lg">
          <p className="text-xs text-foreground-muted mb-1">Frequency</p>
          <p className="text-sm font-medium text-foreground capitalize">{report.frequency}</p>
        </div>
        <div className="p-2 bg-surface-muted rounded-lg">
          <p className="text-xs text-foreground-muted mb-1">Format</p>
          <p className="text-sm font-medium text-foreground uppercase">{report.format}</p>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1 text-foreground-muted">
          <Clock className="w-3 h-3" />
          <span>Next: {report.nextRun.toLocaleDateString()}</span>
        </div>
        <div className="flex items-center gap-1 text-foreground-muted">
          <Users className="w-3 h-3" />
          <span>{report.recipients.length} recipients</span>
        </div>
      </div>
    </div>
  );
};

const AlertCard: React.FC<{
  alert: Alert;
  onEdit: () => void;
  onDelete: () => void;
  onToggle: () => void;
}> = ({ alert, onEdit, onDelete, onToggle }) => {
  const priority = PRIORITIES.find(p => p.value === alert.priority);
  const operator = OPERATORS.find(o => o.value === alert.operator);

  return (
    <div className={`bg-surface border rounded-xl p-4 transition-all ${
      alert.isActive ? 'border-border' : 'border-border/50 opacity-60'
    }`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${priority?.color || 'bg-surface-muted'}`}>
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{alert.name}</h3>
            <p className="text-xs text-foreground-muted">
              {alert.metric} {operator?.symbol} {alert.threshold}
              {alert.operator.includes('percent') ? '%' : ''}
            </p>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded ${priority?.color}`}>
          {priority?.label}
        </span>
      </div>

      <div className="flex items-center gap-2 mb-3">
        {alert.channels.map((channel) => (
          <span
            key={channel}
            className="px-2 py-1 text-xs bg-surface-muted text-foreground-muted rounded capitalize"
          >
            {channel}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggle}
            className={`p-1.5 rounded transition-colors ${
              alert.isActive
                ? 'bg-emerald-500/10 text-emerald-500'
                : 'bg-surface-muted text-foreground-muted'
            }`}
          >
            {alert.isActive ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <button onClick={onEdit} className="p-1.5 hover:bg-surface-hover rounded">
            <Edit3 className="w-4 h-4 text-foreground-muted" />
          </button>
          <button onClick={onDelete} className="p-1.5 hover:bg-red-500/10 rounded">
            <Trash2 className="w-4 h-4 text-red-500" />
          </button>
        </div>
        <div className="text-xs text-foreground-muted">
          Triggered {alert.triggerCount} times
        </div>
      </div>
    </div>
  );
};

const AlertHistoryRow: React.FC<{
  history: AlertHistory;
  onAcknowledge: () => void;
}> = ({ history, onAcknowledge }) => {
  const statusColors = {
    triggered: 'text-red-500 bg-red-500/10',
    resolved: 'text-emerald-500 bg-emerald-500/10',
    acknowledged: 'text-amber-500 bg-amber-500/10',
  };

  return (
    <div className="flex items-center gap-4 p-4 bg-surface border border-border rounded-lg">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${statusColors[history.status]}`}>
        {history.status === 'triggered' && <AlertTriangle className="w-4 h-4" />}
        {history.status === 'resolved' && <CheckCircle className="w-4 h-4" />}
        {history.status === 'acknowledged' && <Eye className="w-4 h-4" />}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-foreground">{history.alertName}</p>
        <p className="text-xs text-foreground-muted">{history.message}</p>
      </div>
      <div className="text-right">
        <p className="text-sm text-foreground">
          {history.value.toLocaleString()} (threshold: {history.threshold.toLocaleString()})
        </p>
        <p className="text-xs text-foreground-muted">
          {history.triggeredAt.toLocaleString()}
        </p>
      </div>
      {history.status === 'triggered' && (
        <button
          onClick={onAcknowledge}
          className="px-3 py-1.5 text-xs font-medium bg-brand-600 text-white rounded hover:bg-brand-500 transition-colors"
        >
          Acknowledge
        </button>
      )}
    </div>
  );
};

// =============================================================================
// MODAL COMPONENTS
// =============================================================================

interface CreateReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (report: Partial<ScheduledReport>) => void;
  editingReport?: ScheduledReport;
}

const CreateReportModal: React.FC<CreateReportModalProps> = ({
  isOpen,
  onClose,
  onSave,
  editingReport,
}) => {
  const [name, setName] = useState(editingReport?.name || '');
  const [description, setDescription] = useState(editingReport?.description || '');
  const [frequency, setFrequency] = useState<ReportFrequency>(editingReport?.frequency || 'weekly');
  const [format, setFormat] = useState<'pdf' | 'excel' | 'html'>(editingReport?.format || 'pdf');
  const [recipients, setRecipients] = useState(editingReport?.recipients.join(', ') || '');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(editingReport?.metrics || []);

  useEffect(() => {
    if (editingReport) {
      setName(editingReport.name);
      setDescription(editingReport.description);
      setFrequency(editingReport.frequency);
      setFormat(editingReport.format);
      setRecipients(editingReport.recipients.join(', '));
      setSelectedMetrics(editingReport.metrics);
    }
  }, [editingReport]);

  const handleSave = () => {
    onSave({
      name,
      description,
      frequency,
      format,
      recipients: recipients.split(',').map(r => r.trim()).filter(Boolean),
      metrics: selectedMetrics,
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface border border-border rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
      >
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-foreground">
              {editingReport ? 'Edit Report' : 'Create Scheduled Report'}
            </h2>
            <button onClick={onClose} className="p-1 hover:bg-surface-hover rounded">
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Report Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Weekly Sales Summary"
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the report..."
              rows={2}
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Frequency</label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value as ReportFrequency)}
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              >
                {FREQUENCIES.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Format</label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value as 'pdf' | 'excel' | 'html')}
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              >
                <option value="pdf">PDF</option>
                <option value="excel">Excel</option>
                <option value="html">HTML Email</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Recipients (comma-separated)</label>
            <input
              type="text"
              value={recipients}
              onChange={(e) => setRecipients(e.target.value)}
              placeholder="email1@example.com, email2@example.com"
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Metrics to Include</label>
            <div className="grid grid-cols-2 gap-2">
              {SAMPLE_METRICS.map((metric) => (
                <label
                  key={metric}
                  className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
                    selectedMetrics.includes(metric)
                      ? 'bg-brand-600/10 border border-brand-500'
                      : 'bg-surface-muted border border-transparent hover:border-border'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedMetrics.includes(metric)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedMetrics([...selectedMetrics, metric]);
                      } else {
                        setSelectedMetrics(selectedMetrics.filter(m => m !== metric));
                      }
                    }}
                    className="w-4 h-4 accent-brand-600"
                  />
                  <span className="text-sm text-foreground">{metric}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-border flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!name || !recipients || selectedMetrics.length === 0}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            {editingReport ? 'Save Changes' : 'Create Report'}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

interface CreateAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (alert: Partial<Alert>) => void;
  editingAlert?: Alert;
}

const CreateAlertModal: React.FC<CreateAlertModalProps> = ({
  isOpen,
  onClose,
  onSave,
  editingAlert,
}) => {
  const [name, setName] = useState(editingAlert?.name || '');
  const [metric, setMetric] = useState(editingAlert?.metric || SAMPLE_METRICS[0]);
  const [operator, setOperator] = useState<AlertOperator>(editingAlert?.operator || 'greater_than');
  const [threshold, setThreshold] = useState(editingAlert?.threshold?.toString() || '');
  const [priority, setPriority] = useState<AlertPriority>(editingAlert?.priority || 'medium');
  const [channels, setChannels] = useState<DeliveryChannel[]>(editingAlert?.channels || ['email']);
  const [recipients, setRecipients] = useState(editingAlert?.recipients.join(', ') || '');

  const handleSave = () => {
    onSave({
      name,
      metric,
      operator,
      threshold: parseFloat(threshold),
      priority,
      channels,
      recipients: recipients.split(',').map(r => r.trim()).filter(Boolean),
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface border border-border rounded-2xl w-full max-w-lg"
      >
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-foreground">
              {editingAlert ? 'Edit Alert' : 'Create Alert'}
            </h2>
            <button onClick={onClose} className="p-1 hover:bg-surface-hover rounded">
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Alert Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., High Revenue Alert"
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Metric</label>
              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              >
                {SAMPLE_METRICS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as AlertPriority)}
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              >
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Condition</label>
              <select
                value={operator}
                onChange={(e) => setOperator(e.target.value as AlertOperator)}
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              >
                {OPERATORS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Threshold</label>
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                placeholder="e.g., 10000"
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Delivery Channels</label>
            <div className="flex gap-2">
              {(['email', 'slack', 'teams', 'webhook'] as DeliveryChannel[]).map((channel) => (
                <button
                  key={channel}
                  onClick={() => {
                    if (channels.includes(channel)) {
                      setChannels(channels.filter(c => c !== channel));
                    } else {
                      setChannels([...channels, channel]);
                    }
                  }}
                  className={`px-3 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                    channels.includes(channel)
                      ? 'bg-brand-600/10 text-brand-500 border border-brand-500'
                      : 'bg-surface-muted text-foreground-muted border border-transparent'
                  }`}
                >
                  {channel}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Recipients</label>
            <input
              type="text"
              value={recipients}
              onChange={(e) => setRecipients(e.target.value)}
              placeholder="email1@example.com, email2@example.com"
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
            />
          </div>
        </div>

        <div className="p-6 border-t border-border flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!name || !threshold || channels.length === 0}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            {editingAlert ? 'Save Changes' : 'Create Alert'}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// =============================================================================
// MAIN REPORTS PAGE
// =============================================================================

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<'reports' | 'alerts' | 'history'>('reports');
  const [reports, setReports] = useState<ScheduledReport[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertHistory, setAlertHistory] = useState<AlertHistory[]>([]);
  const [showCreateReport, setShowCreateReport] = useState(false);
  const [showCreateAlert, setShowCreateAlert] = useState(false);
  const [editingReport, setEditingReport] = useState<ScheduledReport | undefined>();
  const [editingAlert, setEditingAlert] = useState<Alert | undefined>();
  const [searchQuery, setSearchQuery] = useState('');

  // Initialize with sample data
  useEffect(() => {
    setReports([
      {
        id: 'report-1',
        name: 'Weekly Sales Summary',
        description: 'Comprehensive sales metrics and trends',
        frequency: 'weekly',
        nextRun: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000),
        lastRun: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000),
        recipients: ['team@company.com', 'manager@company.com'],
        metrics: ['Total Revenue', 'Monthly Sales', 'Conversion Rate'],
        format: 'pdf',
        isActive: true,
        createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      },
      {
        id: 'report-2',
        name: 'Monthly KPI Dashboard',
        description: 'Executive KPI overview',
        frequency: 'monthly',
        nextRun: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000),
        recipients: ['executives@company.com'],
        metrics: ['Net Profit Margin', 'Customer Count', 'Churn Rate'],
        format: 'excel',
        isActive: true,
        createdAt: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
      },
    ]);

    setAlerts([
      {
        id: 'alert-1',
        name: 'Revenue Threshold Alert',
        metric: 'Total Revenue',
        operator: 'greater_than',
        threshold: 100000,
        priority: 'high',
        channels: ['email', 'slack'],
        recipients: ['team@company.com'],
        isActive: true,
        lastTriggered: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
        triggerCount: 5,
        createdAt: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000),
      },
      {
        id: 'alert-2',
        name: 'Low Inventory Warning',
        metric: 'Inventory Levels',
        operator: 'less_than',
        threshold: 100,
        priority: 'critical',
        channels: ['email'],
        recipients: ['operations@company.com'],
        isActive: true,
        triggerCount: 2,
        createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
      },
    ]);

    setAlertHistory([
      {
        id: 'history-1',
        alertId: 'alert-1',
        alertName: 'Revenue Threshold Alert',
        triggeredAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
        value: 125000,
        threshold: 100000,
        status: 'triggered',
        message: 'Total Revenue exceeded threshold by 25%',
      },
      {
        id: 'history-2',
        alertId: 'alert-2',
        alertName: 'Low Inventory Warning',
        triggeredAt: new Date(Date.now() - 24 * 60 * 60 * 1000),
        value: 85,
        threshold: 100,
        status: 'acknowledged',
        message: 'Inventory levels dropped below minimum threshold',
      },
    ]);
  }, []);

  // Report handlers
  const handleSaveReport = useCallback((reportData: Partial<ScheduledReport>) => {
    if (editingReport) {
      setReports(prev => prev.map(r =>
        r.id === editingReport.id ? { ...r, ...reportData } : r
      ));
    } else {
      const newReport: ScheduledReport = {
        id: `report-${Date.now()}`,
        name: reportData.name || 'New Report',
        description: reportData.description || '',
        frequency: reportData.frequency || 'weekly',
        nextRun: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        recipients: reportData.recipients || [],
        metrics: reportData.metrics || [],
        format: reportData.format || 'pdf',
        isActive: true,
        createdAt: new Date(),
      };
      setReports(prev => [...prev, newReport]);
    }
    setEditingReport(undefined);
  }, [editingReport]);

  const handleDeleteReport = useCallback((id: string) => {
    setReports(prev => prev.filter(r => r.id !== id));
  }, []);

  const handleToggleReport = useCallback((id: string) => {
    setReports(prev => prev.map(r =>
      r.id === id ? { ...r, isActive: !r.isActive } : r
    ));
  }, []);

  // Alert handlers
  const handleSaveAlert = useCallback((alertData: Partial<Alert>) => {
    if (editingAlert) {
      setAlerts(prev => prev.map(a =>
        a.id === editingAlert.id ? { ...a, ...alertData } : a
      ));
    } else {
      const newAlert: Alert = {
        id: `alert-${Date.now()}`,
        name: alertData.name || 'New Alert',
        metric: alertData.metric || SAMPLE_METRICS[0],
        operator: alertData.operator || 'greater_than',
        threshold: alertData.threshold || 0,
        priority: alertData.priority || 'medium',
        channels: alertData.channels || ['email'],
        recipients: alertData.recipients || [],
        isActive: true,
        triggerCount: 0,
        createdAt: new Date(),
      };
      setAlerts(prev => [...prev, newAlert]);
    }
    setEditingAlert(undefined);
  }, [editingAlert]);

  const handleDeleteAlert = useCallback((id: string) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  }, []);

  const handleToggleAlert = useCallback((id: string) => {
    setAlerts(prev => prev.map(a =>
      a.id === id ? { ...a, isActive: !a.isActive } : a
    ));
  }, []);

  const handleAcknowledgeAlert = useCallback((id: string) => {
    setAlertHistory(prev => prev.map(h =>
      h.id === id ? { ...h, status: 'acknowledged' } : h
    ));
  }, []);

  const filteredReports = reports.filter(r =>
    r.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredAlerts = alerts.filter(a =>
    a.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeAlertsCount = alertHistory.filter(h => h.status === 'triggered').length;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-hidden bg-background flex flex-col">
        {/* Header */}
        <div className="border-b border-border p-6">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">Reports & Alerts</h1>
              <p className="text-foreground-secondary">
                Schedule automated reports and set up threshold alerts
              </p>
            </div>
            <div className="flex items-center gap-3">
              {activeAlertsCount > 0 && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-full">
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                  <span className="text-sm font-medium text-red-500">
                    {activeAlertsCount} active alert{activeAlertsCount !== 1 ? 's' : ''}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-border px-6">
          <div className="flex items-center gap-6 max-w-7xl mx-auto">
            {[
              { id: 'reports', label: 'Scheduled Reports', icon: Calendar, count: reports.length },
              { id: 'alerts', label: 'Alerts', icon: Bell, count: alerts.length },
              { id: 'history', label: 'Alert History', icon: Clock, count: alertHistory.length },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-4 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-brand-500 text-brand-500'
                    : 'border-transparent text-foreground-muted hover:text-foreground'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
                <span className="px-2 py-0.5 text-xs bg-surface-muted rounded-full">
                  {tab.count}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto">
            {/* Search and Actions */}
            <div className="flex items-center justify-between mb-6">
              <div className="relative w-80">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search..."
                  className="w-full pl-10 pr-4 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                />
              </div>
              {activeTab === 'reports' && (
                <button
                  onClick={() => setShowCreateReport(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  New Report
                </button>
              )}
              {activeTab === 'alerts' && (
                <button
                  onClick={() => setShowCreateAlert(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  New Alert
                </button>
              )}
            </div>

            {/* Reports Tab */}
            {activeTab === 'reports' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredReports.length === 0 ? (
                  <div className="col-span-full text-center py-16">
                    <Calendar className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
                    <p className="text-foreground-muted">No scheduled reports yet</p>
                    <button
                      onClick={() => setShowCreateReport(true)}
                      className="mt-4 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors"
                    >
                      Create Your First Report
                    </button>
                  </div>
                ) : (
                  filteredReports.map((report) => (
                    <ReportCard
                      key={report.id}
                      report={report}
                      onEdit={() => {
                        setEditingReport(report);
                        setShowCreateReport(true);
                      }}
                      onDelete={() => handleDeleteReport(report.id)}
                      onToggle={() => handleToggleReport(report.id)}
                      onRunNow={() => console.log('Run now:', report.id)}
                    />
                  ))
                )}
              </div>
            )}

            {/* Alerts Tab */}
            {activeTab === 'alerts' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredAlerts.length === 0 ? (
                  <div className="col-span-full text-center py-16">
                    <Bell className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
                    <p className="text-foreground-muted">No alerts configured yet</p>
                    <button
                      onClick={() => setShowCreateAlert(true)}
                      className="mt-4 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors"
                    >
                      Create Your First Alert
                    </button>
                  </div>
                ) : (
                  filteredAlerts.map((alert) => (
                    <AlertCard
                      key={alert.id}
                      alert={alert}
                      onEdit={() => {
                        setEditingAlert(alert);
                        setShowCreateAlert(true);
                      }}
                      onDelete={() => handleDeleteAlert(alert.id)}
                      onToggle={() => handleToggleAlert(alert.id)}
                    />
                  ))
                )}
              </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <div className="space-y-3">
                {alertHistory.length === 0 ? (
                  <div className="text-center py-16">
                    <Clock className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
                    <p className="text-foreground-muted">No alert history yet</p>
                  </div>
                ) : (
                  alertHistory.map((history) => (
                    <AlertHistoryRow
                      key={history.id}
                      history={history}
                      onAcknowledge={() => handleAcknowledgeAlert(history.id)}
                    />
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Modals */}
      <CreateReportModal
        isOpen={showCreateReport}
        onClose={() => {
          setShowCreateReport(false);
          setEditingReport(undefined);
        }}
        onSave={handleSaveReport}
        editingReport={editingReport}
      />

      <CreateAlertModal
        isOpen={showCreateAlert}
        onClose={() => {
          setShowCreateAlert(false);
          setEditingAlert(undefined);
        }}
        onSave={handleSaveAlert}
        editingAlert={editingAlert}
      />
    </div>
  );
}
