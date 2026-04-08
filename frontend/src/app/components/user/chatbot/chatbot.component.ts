import { Component, ElementRef, OnInit, ViewChild, Input, OnDestroy, AfterViewInit ,Output,EventEmitter} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../../services/chat.sevice';
import { switchMap } from 'rxjs';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss'],
})
export class ChatbotComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;
  @Input() userRole: string = 'user';
  @Output() applicationSubmitted = new EventEmitter<void>();

  private observer?: MutationObserver;
  candidateId: number | null = null;
  sessionId = crypto.randomUUID();
  isLoading = false;
  userInput = '';
  resumeUploaded = false;
  messages: { text: string; sender: 'user' | 'bot'; agent?: string }[] = [];

  constructor(private chatService: ChatService) {}

  ngOnInit() {
    // 1. Static Greeting - No API call here
    this.messages.push({
      text: "👋 Hi! I'm your job assistant. Please upload your resume or type a message to get started.",
      sender: 'bot',
    });
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
    this.observer.observe(container, { childList: true, subtree: true });
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (!file) return;

    this.messages.push({ text: `📄 ${file.name}`, sender: 'user' });
    this.messages.push({ text: '📤 Uploading and processing resume...', sender: 'bot' });
    this.isLoading = true;

    this.chatService
      .uploadResume(file, this.sessionId)
      .pipe(
        switchMap((res) => {
          this.candidateId = res.candidate_id;
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
          this.messages.push({ text: res.reply, sender: 'bot' });
          this.resumeUploaded = true;
          this.isLoading = false;
          this.applicationSubmitted.emit();
        },
        error: () => {
          this.messages.push({ text: '⚠️ Resume processing failed.', sender: 'bot' });
          this.isLoading = false;
        },
      });
  }

  sendMessage() {
    if (!this.userInput.trim() || this.isLoading) return;

    const input = this.userInput;
    this.userInput = ''; // Clear input immediately
    this.messages.push({ text: input, sender: 'user' });
    this.isLoading = true;

    this.chatService
      .send(input, this.userRole, this.sessionId, this.candidateId)
      .subscribe({
        next: (res) => {
          this.messages.push({ text: res.reply, sender: 'bot' });
          this.isLoading = false;
        },
        error: () => {
          this.messages.push({ text: '⚠️ Error connecting to assistant.', sender: 'bot' });
          this.isLoading = false;
        },
      });
  }

  private scrollToBottom() {
    const element = this.scrollContainer.nativeElement;
    window.requestAnimationFrame(() => {
      element.scrollTop = element.scrollHeight;
    });
  }

  handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      event.preventDefault();
      this.sendMessage();
    }
  }
}