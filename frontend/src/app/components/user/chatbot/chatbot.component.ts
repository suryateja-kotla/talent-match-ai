import {
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  Input,
  OnDestroy,
  AfterViewInit,
  Output,
  EventEmitter,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { switchMap } from 'rxjs';
import { ChatService } from '../../../services/chat.sevice';
import { JobService } from '../../../services/job.service';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss'],
})
export class ChatbotComponent implements OnInit {
  @ViewChild('scrollContainer') scrollContainer!: ElementRef;
  @ViewChild('fileInput') fileInput!: ElementRef;
  @Input() userRole: string = 'user';
  @Output() applicationSubmitted = new EventEmitter<void>();

  private observer?: MutationObserver;
  candidateId: number | null = null;
  sessionId = crypto.randomUUID();
  isLoading = false;
  userInput = '';
  resumeUploaded = false;
  messages: { text: string; sender: 'user' | 'bot'; agent?: string }[] = [];

  constructor(
    private chatService: ChatService,
    private jobService: JobService,
  ) {}

  ngOnInit() {
    // 1. Static Greeting
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

    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }
    this.messages.push({ text: file.name, sender: 'user' });

    this.messages.push({ text: '📤 Uploading resume...', sender: 'bot' });
    this.isLoading = true;

    this.chatService
      .uploadResume(file, this.sessionId)
      .pipe(
        switchMap((res) => {
          this.candidateId = res.candidate_id;
          return this.chatService.send(
            'resume uploaded.',
            'user',
            this.sessionId,
            this.candidateId,
          );
        }),
      )
      .subscribe({
        next: (res) => {
          this.messages.push({ text: res.reply, sender: 'bot' });
          localStorage.setItem('candidate_id', String(this.candidateId));
          this.resumeUploaded = true;
          this.isLoading = false;
          setTimeout(() => {
            this.applicationSubmitted.emit();
          }, 500);
          this.jobService.triggerRefresh();
        },
        error: () => {
          this.messages.push({
            text: '⚠️ Resume processing failed.',
            sender: 'bot',
          });
          this.isLoading = false;
        },
      });
  }

  sendMessage() {
    if (!this.userInput.trim() || this.isLoading) return;

    const input = this.userInput;
    this.userInput = '';
    this.messages.push({ text: input, sender: 'user' });
    this.isLoading = true;

    this.chatService
      .send(input, this.userRole, this.sessionId, this.candidateId)
      .subscribe({
        next: (res) => {
          this.messages.push({ text: res.reply, sender: 'bot' });
          this.isLoading = false;
          if (res.reply.toLowerCase().includes('applied')) {
            console.log('Application detected → refreshing UI');

            setTimeout(() => {
              this.applicationSubmitted.emit(); // parent event
              this.jobService.triggerRefresh(); // direct refresh
            }, 400);
          }
        },
        error: () => {
          this.messages.push({
            text: '⚠️ Error connecting to assistant.',
            sender: 'bot',
          });
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
