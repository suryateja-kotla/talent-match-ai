import {
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  OnDestroy,
  AfterViewInit,
} from '@angular/core';
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
export class HrChatComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;
  @Output() jobCreated = new EventEmitter<void>();

  private observer?: MutationObserver;

  sessionId = crypto.randomUUID();
  isLoading = false;
  userInput = '';
  messages: { from: 'user' | 'bot'; text: string }[] = [];

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.messages.push({
      from: 'bot',
      text: 'Hi, I am HR assistant. How can I help you create a job today?',
    });

    this.isLoading = false;
  }

  ngAfterViewInit() {
    this.setupScrollObserver();
  }

  ngOnDestroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }

  private setupScrollObserver() {
    const container = this.scrollContainer.nativeElement;
    this.observer = new MutationObserver(() => {
      this.scrollToBottom();
    });

    this.observer.observe(container, {
      childList: true,
      subtree: true,
    });
  }

  sendMessage(): void {
    if (!this.userInput.trim()) return;

    const input = this.userInput;
    this.userInput = '';

    // Add user message to UI
    this.messages.push({ from: 'user', text: input });

    this.isLoading = true;

    this.chatService.send(input, 'hr', this.sessionId).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.messages.push({ from: 'bot', text: res.reply });

        if (res.reply?.toLowerCase().includes('created')) {
          this.jobCreated.emit();
        }
      },
      error: () => {
        this.isLoading = false;
        this.messages.push({ from: 'bot', text: 'Something went wrong.' });
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
    }, 50);
  }
}
