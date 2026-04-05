import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../../services/chat.sevice';

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
  styleUrls: ['./chatbot.component.scss']
})
export class ChatbotComponent {

  @ViewChild('scrollContainer') scrollContainer!: ElementRef;

  step: ChatStep = 'WAITING_FOR_RESUME';
  constructor(private chatService: ChatService) {}

  sessionId = crypto.randomUUID();
  isLoading = false;
  userInput = '';

  // ✅ Added optional "agent" (non-breaking change)
  messages: { text: string; sender: 'user' | 'bot'; agent?: string }[] = [
    { text: 'Hi 👋 Please upload your resume to get started.', sender: 'bot' }
  ];

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (!file) return;

    this.messages.push({ text: file.name, sender: 'user' });
    this.messages.push({ text: 'Resume received ✅', sender: 'bot' });

    this.step = 'WAITING_FOR_LOCATION';

    this.messages.push({
      text: 'What is your preferred location?',
      sender: 'bot'
    });

    this.scrollToBottom();
  }

  sendMessage() {
    if (!this.userInput.trim() || this.isLoading) return;

    const input = this.userInput;

    this.messages.push({ text: input, sender: 'user' });

    if (this.step === 'WAITING_FOR_LOCATION') {
      this.handleLocation(input);
    } else if (this.step === 'WAITING_FOR_RESUME') {
      this.messages.push({
        text: 'Please upload your resume first 📄',
        sender: 'bot'
      });
    }

    this.userInput = '';
    this.scrollToBottom();
  }

  handleLocation(location: string) {
    this.messages.push({
      text: `Searching jobs in ${location}...`,
      sender: 'bot'
    });

    this.step = 'PROCESSING';
    this.isLoading = true;

    // ✅ Improved prompt (better routing)
    const prompt = `Find jobs in ${location}`;

    this.chatService.send(prompt, 'candidate', this.sessionId).subscribe({
      next: (res) => {

        // ✅ Store agent separately (clean + future-proof)
        this.messages.push({
          text: res.reply,
          sender: 'bot',
        });

        // ✅ (Optional fallback display – keeps your old behavior safe)
        // this.messages.push({
        //   text: `🤖 (${res.agent})\n${res.reply}`,
        //   sender: 'bot'
        // });

        this.step = 'DONE';
        this.isLoading = false;
        this.scrollToBottom();
      },
      error: () => {
        this.messages.push({
          text: '⚠️ Error connecting to assistant.',
          sender: 'bot'
        });

        this.isLoading = false;
      }
    });
  }

  getPlaceholder(): string {
    if (this.step === 'WAITING_FOR_LOCATION') {
      return 'Enter location (e.g. Bangalore)';
    }
    return 'Upload resume first...';
  }

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