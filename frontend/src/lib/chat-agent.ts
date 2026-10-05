import {
  HttpAgent,
  type HttpAgentConfig,
  type RunAgentInput,
} from "@ag-ui/client"

// Chat agent that sends only the newest message and keeps its own order of messages.
export class ChatAgent extends HttpAgent {
  constructor(config: HttpAgentConfig) {
    super(config)
    this.subscribe({
      onMessagesSnapshotEvent: () => ({ stopPropagation: true }),
    })
  }

  protected override requestInit(input: RunAgentInput) {
    return super.requestInit({
      ...input,
      messages: input.messages.slice(-1),
      state: {},
    })
  }
}
