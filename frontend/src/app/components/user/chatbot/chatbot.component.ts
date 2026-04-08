import { Component, ElementRef, OnInit, ViewChild, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../../services/chat.sevice';
import { switchMap } from 'rxjs';

type ChatStep =
  | 'WAITING_FOR_RESUME'
  | 'WAITING_FOR_LOCATION'
  | 'PROCESSING'
  | 'DONE';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss'],
})
export class ChatbotComponent implements OnInit {
  @ViewChild('scrollContainer') scrollContainer!: ElementRef;
  @Input() userRole: string = 'user';

  //step: ChatStep = 'WAITING_FOR_RESUME';
  constructor(private chatService: ChatService) {}
  candidateId: number | null = null;
  sessionId = crypto.randomUUID();
  isLoading = false;
  userInput = '';
  resumeUploaded = false;

  ngOnInit() {
    this.messages.push({
      text: 'Connecting to assistant...',
      sender: 'bot',
    });

    this.isLoading = true;

    const initialMessage = 'start';

    this.chatService
      .send(initialMessage, this.userRole, this.sessionId)
      .subscribe({
        next: (res) => {
          this.messages = [
            {
              text: res.reply,
              sender: 'bot',
            },
          ];

          this.isLoading = false;
          this.scrollToBottom();
        },
        error: () => {
          this.messages = [
            {
              text: '⚠️ Failed to connect to assistant.',
              sender: 'bot',
            },
          ];

          this.isLoading = false;
        },
      });
  }
  // // ✅ Added optional "agent" (non-breaking change)
  // messages: { text: string; sender: 'user' | 'bot'; agent?: string }[] = [
  //   { text: 'Hi 👋 Please upload your resume to get started.', sender: 'bot' },
  // ];
  messages: { text: string; sender: 'user' | 'bot'; agent?: string }[] = [];

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (!file) return;

    // ✅ Step 1 — show filename
    this.messages.push({ text: file.name, sender: 'user' });

    // ✅ Step 2 — show uploading
    this.messages.push({ text: '📤 Uploading resume...', sender: 'bot' });
    this.isLoading = true;
    this.scrollToBottom();

    this.chatService
      .uploadResume(file, this.sessionId)
      .pipe(
        switchMap((res) => {
          this.candidateId = res.candidate_id;

          // ✅ Step 3 — replace uploading with processing
          this.messages.push({
            text: '⚙️ Processing your resume...',
            sender: 'bot',
          });
          this.scrollToBottom();

          return this.chatService.send(
            'resume uploaded',
            'user',
            this.sessionId,
            this.candidateId,
          );
        }),
      )
      .subscribe({
        next: (res) => {
          // ✅ Step 4 — show processed
          this.messages.push({
            text: '✅ Resume processed successfully!',
            sender: 'bot',
          });

          // ✅ Step 5 — show agent reply
          this.messages.push({ text: res.reply, sender: 'bot' });

          this.resumeUploaded = true;
          this.isLoading = false;
          this.scrollToBottom();
        },
        error: () => {
          this.messages.push({
            text: '⚠️ Resume upload or processing failed.',
            sender: 'bot',
          });
          this.isLoading = false;
        },
      });
  }
  sendMessage() {
    if (!this.userInput.trim() || this.isLoading) return;

    const input = this.userInput;

    this.messages.push({ text: input, sender: 'user' });

    this.isLoading = true;

    // 🔥 DIRECT API CALL (no step restriction)
    this.chatService
      .send(input, this.userRole, this.sessionId, this.candidateId)
      .subscribe({
        next: (res) => {
          this.messages.push({
            text: res.reply,
            sender: 'bot',
          });

          this.isLoading = false;
          this.scrollToBottom();
        },
        error: () => {
          this.messages.push({
            text: '⚠️ Error connecting to assistant.',
            sender: 'bot',
          });

          this.isLoading = false;
        },
      });

    this.userInput = '';
    this.scrollToBottom();
  }

  // handleLocation(location: string) {
  //   this.messages.push({
  //     text: `Searching jobs in ${location}...`,
  //     sender: 'bot',
  //   });

  //   this.step = 'PROCESSING';
  //   this.isLoading = true;

  //   // ✅ Improved prompt (better routing)
  //   const prompt = `Find jobs in ${location}`;

  //   this.chatService.send(prompt, 'user', this.sessionId,this.candidateId).subscribe({
  //     next: (res) => {
  //       // ✅ Store agent separately (clean + future-proof)
  //       this.messages.push({
  //         text: res.reply,
  //         sender: 'bot',
  //       });

  //       this.step = 'DONE';
  //       this.isLoading = false;
  //       this.scrollToBottom();
  //     },
  //     error: () => {
  //       this.messages.push({
  //         text: '⚠️ Error connecting to assistant.',
  //         sender: 'bot',
  //       });

  //       this.isLoading = false;
  //     },
  //   });
  // }

  // getPlaceholder(): string {
  //   if (this.step === 'WAITING_FOR_LOCATION') {
  //     return 'Enter location (e.g. Bangalore)';
  //   }
  //   return 'Upload resume first...';
  // }

  scrollToBottom() {
    setTimeout(() => {
      this.scrollContainer.nativeElement.scrollTop =
        this.scrollContainer.nativeElement.scrollHeight;
    }, 100);
  }

  handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      event.preventDefault();
      this.sendMessage();
    }
  }
}
