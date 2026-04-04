import { CommonModule } from '@angular/common';

import { Component } from '@angular/core';

import { FormsModule } from '@angular/forms';

import { AuthService } from '../../services/auth.service';
import { ChatService } from '../../services/chat.sevice';

interface Message {
  text: string;

  from: 'user' | 'bot';
}

@Component({
  selector: 'app-hr',

  standalone: true,

  imports: [CommonModule, FormsModule], // ✅ added FormsModule for [(ngModel)]

  templateUrl: './hr.component.html',

  styleUrl: './hr.component.scss',
})
export class HrComponent {
  // ✅ Chat state

  userInput = '';

  isLoading = false;

  sessionId = crypto.randomUUID();

  messages: Message[] = [
    {
      text: "👋 Hi! I'm your hiring assistant. Describe the role you want to post and I'll create a job card for you.",
      from: 'bot',
    },
  ];

  // ✅ Your existing jobs

  jobs = [
    {
      title: 'Senior Frontend Developer',

      skills: ['React', 'TypeScript', 'Next.js'],

      exp: '5+ yrs',

      location: 'San Francisco',

      positions: 2,

      applicants: 12,
    },

    {
      title: 'Full Stack Engineer',

      skills: ['Node.js', 'React', 'Docker'],

      exp: '3+ yrs',

      location: 'Remote',

      positions: 3,

      applicants: 24,
    },

    {
      title: 'UX Designer',

      skills: ['Figma', 'Research', 'Prototyping'],

      exp: '4+ yrs',

      location: 'New York',

      positions: 1,

      applicants: 8,
    },
  ];

  constructor(
    private auth: AuthService,

    private chatService: ChatService, // ✅ inject ChatService
  ) {}

  // ✅ Send message to root_agent via FastAPI

  sendMessage() {
    const text = this.userInput.trim();

    if (!text || this.isLoading) return;

    this.messages.push({ text, from: 'user' });

    this.userInput = '';

    this.isLoading = true;

    this.chatService.send(text, 'hr', this.sessionId).subscribe({
      next: (res) => {
        this.messages.push({ text: res.reply, from: 'bot' });

        this.isLoading = false;
      },

      error: () => {
        this.messages.push({
          text: '⚠️ Error connecting to assistant.',
          from: 'bot',
        });

        this.isLoading = false;
      },
    });
  }

  logout() {
    this.auth.logout();
  }
}
