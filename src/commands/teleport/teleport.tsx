import * as React from 'react'
import type { LocalJSXCommandContext } from '../../commands.js'
import { TeleportResumeWrapper } from '../../components/TeleportResumeWrapper.js'
import type { LocalJSXCommandOnDone } from '../../types/command.js'
import type { TeleportRemoteResponse } from '../../utils/conversationRecovery.js'
import {
  checkOutTeleportedSessionBranch,
  processMessagesForTeleportResume,
} from '../../utils/teleport.js'

export async function call(
  onDone: LocalJSXCommandOnDone,
  context: LocalJSXCommandContext,
): Promise<React.ReactNode> {
  const handleComplete = async (result: TeleportRemoteResponse) => {
    const { branchError } = await checkOutTeleportedSessionBranch(result.branch)
    const messages = processMessagesForTeleportResume(result.log, branchError)
    context.setMessages(() => messages)
    onDone(undefined, { display: 'skip', shouldQuery: true })
  }

  return (
    <TeleportResumeWrapper
      onComplete={handleComplete}
      onCancel={() => onDone()}
      source="localCommand"
      isEmbedded={true}
    />
  )
}
