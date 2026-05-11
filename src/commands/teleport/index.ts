import type { Command } from '../../commands.js'

const teleport = {
  type: 'local-jsx',
  name: 'teleport',
  description: 'Resume a Claude Code web session on this machine',
  isHidden: true,
  availability: ['claude-ai'],
  load: () => import('./teleport.js'),
} satisfies Command

export default teleport
