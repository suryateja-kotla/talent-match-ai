import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

type ChatStep =
  | 'WAITING_FOR_RESUME'
  | 'WAITING_FOR_LOCATION'
  | 'PROCESSING'
  | 'DONE';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [FormsModule,CommonModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss']
})
export class ChatbotComponent {

  @ViewChild('scrollContainer') scrollContainer!: ElementRef;

  step: ChatStep = 'WAITING_FOR_RESUME';

  userInput = '';
  messages: { text: string; sender: 'user' | 'bot' }[] = [
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
    if (!this.userInput.trim()) return;

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

    setTimeout(() => {
      this.messages.push({
        text: 'Applied to 5 matching jobs 🎉',
        sender: 'bot'
      });

      this.step = 'DONE';
      this.scrollToBottom();
    }, 2000);
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
    event.preventDefault(); // 🔥 stops newline
    this.sendMessage();
  }
}
}
