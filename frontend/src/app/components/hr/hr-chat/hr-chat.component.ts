import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../../services/chat.sevice';
import { Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-hr-chat',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './hr-chat.component.html',
  styleUrls: ['./hr-chat.component.scss'],
})
export class HrChatComponent implements OnInit {
  @ViewChild('scrollContainer') scrollContainer!: ElementRef;
  @Output() jobCreated = new EventEmitter<void>();

  constructor(private chatService: ChatService) {}

  sessionId = crypto.randomUUID();
  isLoading = false;
  userInput = '';
  messages: { from: 'user' | 'bot'; text: string }[] = [];

  ngOnInit(): void {
    const initialMessage = 'Hi, I am HR. I want to create a job.';

    this.messages.push({ from: 'user', text: initialMessage });
    this.isLoading = true;

    this.chatService.send(initialMessage, 'hr', this.sessionId).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.messages.push({ from: 'bot', text: res.reply });
        if (res.reply?.toLowerCase().includes('created')) {
          this.jobCreated.emit();
        }
        this.scrollToBottom();
      },
      error: () => {
        this.isLoading = false;
        this.messages.push({
          from: 'bot',
          text: 'Something went wrong.',
        });
      },
    });
  }

  sendMessage(): void {
    if (!this.userInput.trim()) return;

    const input = this.userInput;
    this.userInput = '';

    this.messages.push({ from: 'user', text: input });
    this.isLoading = true;
    this.scrollToBottom();

    this.chatService.send(input, 'hr', this.sessionId).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.messages.push({ from: 'bot', text: res.reply });
        this.scrollToBottom();
      },
      error: () => {
        this.isLoading = false;
        this.messages.push({
          from: 'bot',
          text: 'Something went wrong.',
        });
        this.scrollToBottom();
      },
    });
  }
  private scrollToBottom(): void {
    // setTimeout allows Angular's change detection to update the HTML first
    setTimeout(() => {
      try {
        this.scrollContainer.nativeElement.scrollTop =
          this.scrollContainer.nativeElement.scrollHeight;
      } catch (err) {
        console.error('Scroll error:', err);
      }
    }, 50); // 50ms delay is usually perfect
  }
}
