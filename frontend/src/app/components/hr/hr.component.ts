import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-hr',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './hr.component.html',
  styleUrl: './hr.component.scss'
})
export class HrComponent {

  constructor(
    private auth: AuthService,
    private chatService: ChatService
  ) {}

  // 🔹 Chat state
  userInput: string = '';
  messages: any[] = [];

  // 🔹 Dummy jobs (existing UI)
  jobs = [
    {
      title: 'Senior Frontend Developer',
      skills: ['React', 'TypeScript', 'Next.js'],
      exp: '5+ yrs',
      location: 'San Francisco',
      positions: 2,
      applicants: 12
    },
    {
      title: 'Full Stack Engineer',
      skills: ['Node.js', 'React', 'Docker'],
      exp: '3+ yrs',
      location: 'Remote',
      positions: 3,
      applicants: 24
    },
    {
      title: 'UX Designer',
      skills: ['Figma', 'Research', 'Prototyping'],
      exp: '4+ yrs',
      location: 'New York',
      positions: 1,
      applicants: 8
    }
  ];

  // 🔹 Send message to backend
  sendMessage() {
    if (!this.userInput.trim()) return;

    // push user message
    this.messages.push({ sender: 'user', text: this.userInput });

    this.chatService.sendMessage(this.userInput, "hr")
      .subscribe({
        next: (res: any) => {
          this.messages.push({ sender: 'bot', text: res.response });
        },
        error: (err) => {
          console.error(err);
          this.messages.push({ sender: 'bot', text: 'Something went wrong' });
        }
      });

    this.userInput = '';
  }

  logout() {
    this.auth.logout();
  }
}