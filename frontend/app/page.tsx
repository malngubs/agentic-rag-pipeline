/**
 * ============================================================================
 * 🏠 ROOT PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Redirects to the main chat interface.
 */

import { redirect } from 'next/navigation';

export default function HomePage() {
  redirect('/chat');
}
