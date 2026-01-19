/**
 * ============================================================================
 * COLLABORATION - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Team collaboration features:
 * - Share dashboards and analyses
 * - Comments and annotations
 * - Team workspaces
 * - Real-time collaboration indicators
 * - Activity feed
 */

'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Share2,
  MessageSquare,
  Send,
  Plus,
  Settings,
  MoreVertical,
  UserPlus,
  Lock,
  Unlock,
  Globe,
  Link2,
  Copy,
  Check,
  X,
  Eye,
  Edit3,
  Trash2,
  Clock,
  BarChart3,
  FileText,
  Folder,
  ChevronRight,
  Search,
  Filter,
  Bell,
  Heart,
  ThumbsUp,
  Bookmark,
  AtSign,
  Hash,
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

type VisibilityLevel = 'private' | 'team' | 'organization' | 'public';
type ResourceType = 'dashboard' | 'analysis' | 'report' | 'query';
type ActivityType = 'share' | 'comment' | 'edit' | 'view' | 'like' | 'mention';

interface TeamMember {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'owner' | 'admin' | 'editor' | 'viewer';
  isOnline: boolean;
  lastActive?: Date;
}

interface Workspace {
  id: string;
  name: string;
  description: string;
  icon: string;
  members: TeamMember[];
  resourceCount: number;
  createdAt: Date;
  isDefault: boolean;
}

interface SharedResource {
  id: string;
  name: string;
  type: ResourceType;
  description: string;
  visibility: VisibilityLevel;
  owner: TeamMember;
  sharedWith: TeamMember[];
  workspaceId: string;
  createdAt: Date;
  updatedAt: Date;
  viewCount: number;
  likeCount: number;
  commentCount: number;
}

interface Comment {
  id: string;
  resourceId: string;
  author: TeamMember;
  content: string;
  mentions: string[];
  createdAt: Date;
  replies: Comment[];
  likes: number;
}

interface ActivityItem {
  id: string;
  type: ActivityType;
  actor: TeamMember;
  resource?: SharedResource;
  content: string;
  timestamp: Date;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const VISIBILITY_OPTIONS: { value: VisibilityLevel; label: string; description: string; icon: typeof Lock }[] = [
  { value: 'private', label: 'Private', description: 'Only you can access', icon: Lock },
  { value: 'team', label: 'Team', description: 'Workspace members only', icon: Users },
  { value: 'organization', label: 'Organization', description: 'All organization members', icon: Globe },
  { value: 'public', label: 'Public Link', description: 'Anyone with the link', icon: Link2 },
];

const ROLE_COLORS: Record<string, string> = {
  owner: 'bg-purple-500/10 text-purple-500',
  admin: 'bg-blue-500/10 text-blue-500',
  editor: 'bg-emerald-500/10 text-emerald-500',
  viewer: 'bg-gray-500/10 text-gray-500',
};

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

const Avatar: React.FC<{
  user: TeamMember;
  size?: 'sm' | 'md' | 'lg';
  showStatus?: boolean;
}> = ({ user, size = 'md', showStatus = false }) => {
  const sizes = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-10 h-10 text-base',
  };

  return (
    <div className="relative">
      {user.avatar ? (
        <img
          src={user.avatar}
          alt={user.name}
          className={`${sizes[size]} rounded-full object-cover`}
        />
      ) : (
        <div className={`${sizes[size]} rounded-full bg-brand-600/20 flex items-center justify-center font-medium text-brand-500`}>
          {user.name.charAt(0).toUpperCase()}
        </div>
      )}
      {showStatus && (
        <div className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-surface ${
          user.isOnline ? 'bg-emerald-500' : 'bg-gray-400'
        }`} />
      )}
    </div>
  );
};

const WorkspaceCard: React.FC<{
  workspace: Workspace;
  isSelected: boolean;
  onClick: () => void;
}> = ({ workspace, isSelected, onClick }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all ${
      isSelected
        ? 'bg-brand-600/10 border-2 border-brand-500'
        : 'bg-surface border-2 border-transparent hover:border-border'
    }`}
  >
    <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center text-xl">
      {workspace.icon}
    </div>
    <div className="flex-1 text-left">
      <h3 className="font-medium text-foreground">{workspace.name}</h3>
      <p className="text-xs text-foreground-muted">
        {workspace.members.length} members - {workspace.resourceCount} items
      </p>
    </div>
    {workspace.isDefault && (
      <span className="px-2 py-0.5 text-xs bg-brand-600/10 text-brand-500 rounded">
        Default
      </span>
    )}
    <ChevronRight className="w-4 h-4 text-foreground-muted" />
  </button>
);

const ResourceCard: React.FC<{
  resource: SharedResource;
  onView: () => void;
  onShare: () => void;
  onComment: () => void;
}> = ({ resource, onView, onShare, onComment }) => {
  const typeIcons: Record<ResourceType, typeof BarChart3> = {
    dashboard: BarChart3,
    analysis: FileText,
    report: FileText,
    query: Hash,
  };
  const Icon = typeIcons[resource.type];

  return (
    <div className="bg-surface border border-border rounded-xl p-4 hover:border-brand-500/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center">
            <Icon className="w-5 h-5 text-brand-500" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{resource.name}</h3>
            <p className="text-xs text-foreground-muted capitalize">{resource.type}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {VISIBILITY_OPTIONS.find(v => v.value === resource.visibility)?.icon && (
            <span className="p-1">
              {React.createElement(
                VISIBILITY_OPTIONS.find(v => v.value === resource.visibility)!.icon,
                { className: 'w-4 h-4 text-foreground-muted' }
              )}
            </span>
          )}
        </div>
      </div>

      <p className="text-sm text-foreground-secondary mb-3 line-clamp-2">
        {resource.description || 'No description'}
      </p>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Avatar user={resource.owner} size="sm" />
          <span className="text-xs text-foreground-muted">{resource.owner.name}</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-foreground-muted">
          <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" /> {resource.viewCount}
          </span>
          <span className="flex items-center gap-1">
            <ThumbsUp className="w-3 h-3" /> {resource.likeCount}
          </span>
          <span className="flex items-center gap-1">
            <MessageSquare className="w-3 h-3" /> {resource.commentCount}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
        <button
          onClick={onView}
          className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-sm text-foreground hover:bg-surface-hover rounded-lg transition-colors"
        >
          <Eye className="w-4 h-4" /> View
        </button>
        <button
          onClick={onShare}
          className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-sm text-foreground hover:bg-surface-hover rounded-lg transition-colors"
        >
          <Share2 className="w-4 h-4" /> Share
        </button>
        <button
          onClick={onComment}
          className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-sm text-foreground hover:bg-surface-hover rounded-lg transition-colors"
        >
          <MessageSquare className="w-4 h-4" /> Comment
        </button>
      </div>
    </div>
  );
};

const ActivityFeedItem: React.FC<{
  activity: ActivityItem;
}> = ({ activity }) => {
  const activityIcons: Record<ActivityType, typeof Share2> = {
    share: Share2,
    comment: MessageSquare,
    edit: Edit3,
    view: Eye,
    like: ThumbsUp,
    mention: AtSign,
  };
  const Icon = activityIcons[activity.type];

  return (
    <div className="flex items-start gap-3 p-3 hover:bg-surface-hover rounded-lg transition-colors">
      <Avatar user={activity.actor} size="sm" showStatus />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-foreground">
          <span className="font-medium">{activity.actor.name}</span>{' '}
          <span className="text-foreground-muted">{activity.content}</span>
        </p>
        <p className="text-xs text-foreground-muted mt-0.5">
          {formatTimeAgo(activity.timestamp)}
        </p>
      </div>
      <div className="w-8 h-8 rounded-lg bg-surface-muted flex items-center justify-center">
        <Icon className="w-4 h-4 text-foreground-muted" />
      </div>
    </div>
  );
};

const CommentItem: React.FC<{
  comment: Comment;
  onReply: () => void;
  onLike: () => void;
}> = ({ comment, onReply, onLike }) => (
  <div className="flex gap-3 p-3">
    <Avatar user={comment.author} size="sm" />
    <div className="flex-1">
      <div className="flex items-center gap-2 mb-1">
        <span className="font-medium text-sm text-foreground">{comment.author.name}</span>
        <span className="text-xs text-foreground-muted">{formatTimeAgo(comment.createdAt)}</span>
      </div>
      <p className="text-sm text-foreground-secondary">{comment.content}</p>
      <div className="flex items-center gap-4 mt-2">
        <button
          onClick={onLike}
          className="flex items-center gap-1 text-xs text-foreground-muted hover:text-foreground transition-colors"
        >
          <ThumbsUp className="w-3 h-3" /> {comment.likes > 0 && comment.likes}
        </button>
        <button
          onClick={onReply}
          className="flex items-center gap-1 text-xs text-foreground-muted hover:text-foreground transition-colors"
        >
          <MessageSquare className="w-3 h-3" /> Reply
        </button>
      </div>
      {comment.replies.length > 0 && (
        <div className="ml-4 mt-3 space-y-2 border-l-2 border-border pl-4">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              onReply={() => {}}
              onLike={() => {}}
            />
          ))}
        </div>
      )}
    </div>
  </div>
);

// =============================================================================
// MODAL COMPONENTS
// =============================================================================

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  resource?: SharedResource;
}

const ShareModal: React.FC<ShareModalProps> = ({ isOpen, onClose, resource }) => {
  const [visibility, setVisibility] = useState<VisibilityLevel>('team');
  const [email, setEmail] = useState('');
  const [copied, setCopied] = useState(false);
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);

  const shareLink = `https://bi.macrocomm.com/shared/${resource?.id}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(shareLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface border border-border rounded-2xl w-full max-w-md"
      >
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-foreground">Share</h2>
            <button onClick={onClose} className="p-1 hover:bg-surface-hover rounded">
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Visibility */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Visibility</label>
            <div className="grid grid-cols-2 gap-2">
              {VISIBILITY_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setVisibility(option.value)}
                  className={`flex items-center gap-2 p-3 rounded-lg border transition-colors ${
                    visibility === option.value
                      ? 'border-brand-500 bg-brand-600/5'
                      : 'border-border hover:border-border-hover'
                  }`}
                >
                  <option.icon className={`w-4 h-4 ${
                    visibility === option.value ? 'text-brand-500' : 'text-foreground-muted'
                  }`} />
                  <div className="text-left">
                    <p className="text-sm font-medium text-foreground">{option.label}</p>
                    <p className="text-xs text-foreground-muted">{option.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Invite by email */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Invite people</label>
            <div className="flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter email address"
                className="flex-1 px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              />
              <button className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors">
                <UserPlus className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Share link */}
          {(visibility === 'public' || visibility === 'organization') && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Share link</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={shareLink}
                  readOnly
                  className="flex-1 px-3 py-2 bg-surface-muted border border-border rounded-lg text-foreground text-sm"
                />
                <button
                  onClick={handleCopy}
                  className="px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-border flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors"
          >
            Cancel
          </button>
          <button className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors">
            Save Changes
          </button>
        </div>
      </motion.div>
    </div>
  );
};

interface CreateWorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (workspace: Partial<Workspace>) => void;
}

const CreateWorkspaceModal: React.FC<CreateWorkspaceModalProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [icon, setIcon] = useState('folder');

  const icons = ['folder', 'star', 'chart', 'users', 'code', 'rocket', 'heart', 'zap'];

  const handleSave = () => {
    onSave({ name, description, icon });
    onClose();
    setName('');
    setDescription('');
    setIcon('folder');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface border border-border rounded-2xl w-full max-w-md"
      >
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-foreground">Create Workspace</h2>
            <button onClick={onClose} className="p-1 hover:bg-surface-hover rounded">
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Marketing Team"
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is this workspace for?"
              rows={2}
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Icon</label>
            <div className="flex gap-2 flex-wrap">
              {icons.map((i) => (
                <button
                  key={i}
                  onClick={() => setIcon(i)}
                  className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg transition-colors ${
                    icon === i
                      ? 'bg-brand-600/10 border-2 border-brand-500'
                      : 'bg-surface-muted border-2 border-transparent hover:border-border'
                  }`}
                >
                  {i === 'folder' && <Folder className="w-5 h-5" />}
                  {i === 'star' && ''}
                  {i === 'chart' && <BarChart3 className="w-5 h-5" />}
                  {i === 'users' && <Users className="w-5 h-5" />}
                  {i === 'code' && '#'}
                  {i === 'rocket' && ''}
                  {i === 'heart' && <Heart className="w-5 h-5" />}
                  {i === 'zap' && ''}
                </button>
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
            disabled={!name}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            Create Workspace
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

// =============================================================================
// MAIN COLLABORATION PAGE
// =============================================================================

export default function CollaborationPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string | null>(null);
  const [resources, setResources] = useState<SharedResource[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [showShareModal, setShowShareModal] = useState(false);
  const [showCreateWorkspace, setShowCreateWorkspace] = useState(false);
  const [selectedResource, setSelectedResource] = useState<SharedResource | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [newComment, setNewComment] = useState('');

  // Initialize with sample data
  useEffect(() => {
    const currentUser: TeamMember = {
      id: 'user-1',
      name: 'John Doe',
      email: 'john@company.com',
      role: 'owner',
      isOnline: true,
    };

    const sampleMembers: TeamMember[] = [
      currentUser,
      { id: 'user-2', name: 'Sarah Smith', email: 'sarah@company.com', role: 'admin', isOnline: true },
      { id: 'user-3', name: 'Mike Johnson', email: 'mike@company.com', role: 'editor', isOnline: false, lastActive: new Date(Date.now() - 2 * 60 * 60 * 1000) },
      { id: 'user-4', name: 'Emily Brown', email: 'emily@company.com', role: 'viewer', isOnline: true },
    ];

    setWorkspaces([
      {
        id: 'ws-1',
        name: 'General',
        description: 'Default workspace for all team members',
        icon: 'folder',
        members: sampleMembers,
        resourceCount: 12,
        createdAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
        isDefault: true,
      },
      {
        id: 'ws-2',
        name: 'Marketing',
        description: 'Marketing team dashboards and reports',
        icon: 'chart',
        members: sampleMembers.slice(0, 3),
        resourceCount: 8,
        createdAt: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
        isDefault: false,
      },
      {
        id: 'ws-3',
        name: 'Sales Analytics',
        description: 'Sales performance tracking',
        icon: 'star',
        members: sampleMembers.slice(0, 2),
        resourceCount: 5,
        createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        isDefault: false,
      },
    ]);

    setSelectedWorkspace('ws-1');

    setResources([
      {
        id: 'res-1',
        name: 'Q4 Sales Dashboard',
        type: 'dashboard',
        description: 'Comprehensive Q4 sales performance metrics and KPIs',
        visibility: 'team',
        owner: currentUser,
        sharedWith: sampleMembers,
        workspaceId: 'ws-1',
        createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
        viewCount: 145,
        likeCount: 23,
        commentCount: 8,
      },
      {
        id: 'res-2',
        name: 'Customer Churn Analysis',
        type: 'analysis',
        description: 'Analysis of customer churn patterns and retention strategies',
        visibility: 'organization',
        owner: sampleMembers[1],
        sharedWith: sampleMembers.slice(0, 3),
        workspaceId: 'ws-1',
        createdAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
        updatedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
        viewCount: 89,
        likeCount: 15,
        commentCount: 5,
      },
      {
        id: 'res-3',
        name: 'Weekly Revenue Report',
        type: 'report',
        description: 'Automated weekly revenue summary and trends',
        visibility: 'team',
        owner: sampleMembers[2],
        sharedWith: sampleMembers,
        workspaceId: 'ws-1',
        createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
        updatedAt: new Date(Date.now() - 12 * 60 * 60 * 1000),
        viewCount: 67,
        likeCount: 8,
        commentCount: 3,
      },
    ]);

    setActivities([
      {
        id: 'act-1',
        type: 'share',
        actor: currentUser,
        content: 'shared "Q4 Sales Dashboard" with the team',
        timestamp: new Date(Date.now() - 30 * 60 * 1000),
      },
      {
        id: 'act-2',
        type: 'comment',
        actor: sampleMembers[1],
        content: 'commented on "Customer Churn Analysis"',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      },
      {
        id: 'act-3',
        type: 'edit',
        actor: sampleMembers[2],
        content: 'updated "Weekly Revenue Report"',
        timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
      },
      {
        id: 'act-4',
        type: 'like',
        actor: sampleMembers[3],
        content: 'liked "Q4 Sales Dashboard"',
        timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000),
      },
    ]);

    setComments([
      {
        id: 'comment-1',
        resourceId: 'res-1',
        author: sampleMembers[1],
        content: 'Great dashboard! Can we add a regional breakdown?',
        mentions: [],
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
        replies: [
          {
            id: 'comment-1-1',
            resourceId: 'res-1',
            author: currentUser,
            content: 'Sure, I will add that today.',
            mentions: ['Sarah Smith'],
            createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000),
            replies: [],
            likes: 1,
          },
        ],
        likes: 3,
      },
    ]);
  }, []);

  const handleCreateWorkspace = useCallback((data: Partial<Workspace>) => {
    const newWorkspace: Workspace = {
      id: `ws-${Date.now()}`,
      name: data.name || 'New Workspace',
      description: data.description || '',
      icon: data.icon || 'folder',
      members: [],
      resourceCount: 0,
      createdAt: new Date(),
      isDefault: false,
    };
    setWorkspaces(prev => [...prev, newWorkspace]);
    setSelectedWorkspace(newWorkspace.id);
  }, []);

  const handleAddComment = useCallback(() => {
    if (!newComment.trim() || !selectedResource) return;

    const comment: Comment = {
      id: `comment-${Date.now()}`,
      resourceId: selectedResource.id,
      author: {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@company.com',
        role: 'owner',
        isOnline: true,
      },
      content: newComment,
      mentions: [],
      createdAt: new Date(),
      replies: [],
      likes: 0,
    };

    setComments(prev => [comment, ...prev]);
    setNewComment('');
  }, [newComment, selectedResource]);

  const currentWorkspace = workspaces.find(w => w.id === selectedWorkspace);
  const workspaceResources = resources.filter(r => r.workspaceId === selectedWorkspace);
  const filteredResources = workspaceResources.filter(r =>
    r.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-hidden bg-background flex">
        {/* Workspaces sidebar */}
        <div className="w-72 border-r border-border flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-foreground">Workspaces</h2>
              <button
                onClick={() => setShowCreateWorkspace(true)}
                className="p-1.5 hover:bg-surface-hover rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4 text-foreground-muted" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {workspaces.map((workspace) => (
              <WorkspaceCard
                key={workspace.id}
                workspace={workspace}
                isSelected={workspace.id === selectedWorkspace}
                onClick={() => setSelectedWorkspace(workspace.id)}
              />
            ))}
          </div>

          {/* Online members */}
          {currentWorkspace && (
            <div className="p-4 border-t border-border">
              <p className="text-xs font-medium text-foreground-muted mb-3">
                Online ({currentWorkspace.members.filter(m => m.isOnline).length})
              </p>
              <div className="flex -space-x-2">
                {currentWorkspace.members.filter(m => m.isOnline).slice(0, 5).map((member) => (
                  <Avatar key={member.id} user={member} size="sm" showStatus />
                ))}
                {currentWorkspace.members.filter(m => m.isOnline).length > 5 && (
                  <div className="w-6 h-6 rounded-full bg-surface-muted flex items-center justify-center text-xs text-foreground-muted">
                    +{currentWorkspace.members.filter(m => m.isOnline).length - 5}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Main content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-foreground">{currentWorkspace?.name || 'Collaboration'}</h1>
                <p className="text-foreground-secondary">
                  {currentWorkspace?.description || 'Share and collaborate on analyses'}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground-muted" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search resources..."
                    className="w-full pl-10 pr-4 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Resources grid */}
          <div className="flex-1 overflow-auto p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredResources.length === 0 ? (
                <div className="col-span-full text-center py-16">
                  <Folder className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
                  <p className="text-foreground-muted">No shared resources yet</p>
                  <p className="text-sm text-foreground-muted mt-1">
                    Create a dashboard or analysis and share it with your team
                  </p>
                </div>
              ) : (
                filteredResources.map((resource) => (
                  <ResourceCard
                    key={resource.id}
                    resource={resource}
                    onView={() => setSelectedResource(resource)}
                    onShare={() => {
                      setSelectedResource(resource);
                      setShowShareModal(true);
                    }}
                    onComment={() => setSelectedResource(resource)}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        {/* Activity feed sidebar */}
        <div className="w-80 border-l border-border flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-foreground">Activity Feed</h3>
          </div>
          <div className="flex-1 overflow-y-auto">
            {activities.map((activity) => (
              <ActivityFeedItem key={activity.id} activity={activity} />
            ))}
          </div>

          {/* Comments section */}
          {selectedResource && (
            <div className="border-t border-border">
              <div className="p-4 border-b border-border bg-surface-muted">
                <h4 className="text-sm font-medium text-foreground">
                  Comments on {selectedResource.name}
                </h4>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {comments.filter(c => c.resourceId === selectedResource.id).map((comment) => (
                  <CommentItem
                    key={comment.id}
                    comment={comment}
                    onReply={() => {}}
                    onLike={() => {}}
                  />
                ))}
              </div>
              <div className="p-4 border-t border-border">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="flex-1 px-3 py-2 bg-surface border border-border rounded-lg text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                    onKeyPress={(e) => e.key === 'Enter' && handleAddComment()}
                  />
                  <button
                    onClick={handleAddComment}
                    disabled={!newComment.trim()}
                    className="p-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
      <ShareModal
        isOpen={showShareModal}
        onClose={() => {
          setShowShareModal(false);
          setSelectedResource(null);
        }}
        resource={selectedResource || undefined}
      />

      <CreateWorkspaceModal
        isOpen={showCreateWorkspace}
        onClose={() => setShowCreateWorkspace(false)}
        onSave={handleCreateWorkspace}
      />
    </div>
  );
}
