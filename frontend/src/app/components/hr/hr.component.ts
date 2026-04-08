import { CommonModule } from '@angular/common';
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { ChatService } from '../../services/chat.sevice';
import { ViewChild, ElementRef } from '@angular/core';
import { HrChatComponent } from './hr-chat/hr-chat.component';
import { HrJobsComponent } from './hr-jobs/hr-jobs.component';

@Component({
  selector: 'app-hr',
  standalone: true,
  imports: [CommonModule, FormsModule, HrChatComponent, HrJobsComponent],
  templateUrl: './hr.component.html',
  styleUrl: './hr.component.scss',
})
export class HrComponent implements OnInit {
  userInput = '';
  messages: { from: string; text: string }[] = [];
  isLoading = false;
  private sessionId!: string;
  showMobileChat: boolean = false;

  @ViewChild('chatContainer') private chatContainer!: ElementRef;
  @ViewChild(HrJobsComponent) hrJobs!: HrJobsComponent;

  constructor(
    private auth: AuthService,
    private chatService: ChatService,
    private cdr: ChangeDetectorRef,
  ) {
    this.sessionId = this.getOrCreateSessionId();
  }

  ngOnInit(): void {
    // this.loadJobs();
    this.addIntroMessage();
  }

  private getOrCreateSessionId(): string {
    const key = 'chat_session_id';
    let id = localStorage.getItem(key);
    if (!id) {
      const user = this.auth.getCurrentUser();
      id = `hr-${user?.username ?? 'default'}-${Date.now()}`;
      localStorage.setItem(key, id);
    }
    return id;
  }

  sendMessage(): void {
    if (!this.userInput.trim()) return;

    const input = this.userInput;
    this.userInput = '';
    this.messages.push({ from: 'user', text: input });
    this.isLoading = true;
    setTimeout(() => this.scrollToBottom(), 0);

    this.chatService.send(input, 'hr', this.sessionId).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.messages.push({ from: 'bot', text: res.reply || 'Done.' });
        setTimeout(() => this.scrollToBottom(), 0);
        const replyLower = (res.reply || '').toLowerCase();
        if (
          replyLower.includes('created') ||
          replyLower.includes('success') ||
          replyLower.includes('job id')
        ) {
          this.hrJobs.refresh();
        }
      },
      error: () => {
        this.isLoading = false;
        this.messages.push({
          from: 'bot',
          text: '❌ Something went wrong. Please try again.',
        });
        setTimeout(() => this.scrollToBottom(), 0);
      },
    });
  }

  logout(): void {
    this.auth.logout();
  }
  private addIntroMessage(): void {
    if (this.messages.length === 0) {
      this.messages.push({
        from: 'bot',
        text: `👋 Hi! I'm your hiring assistant.

You can describe a role and I'll create a job posting for you.

Example:
"Post a Senior React Developer with 3+ years experience in Bangalore"`,
      });
    }
  }

  private scrollToBottom(): void {
    try {
      this.chatContainer.nativeElement.scrollTop =
        this.chatContainer.nativeElement.scrollHeight;
    } catch (err) {}
  }
  toggleChat() {
    this.showMobileChat = !this.showMobileChat;
  }
}
