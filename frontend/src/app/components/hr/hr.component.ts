import { CommonModule } from '@angular/common';
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { ChatService } from '../../services/chat.sevice';

@Component({
  selector: 'app-hr',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './hr.component.html',
  styleUrl: './hr.component.scss'
})
export class HrComponent implements OnInit {

  userInput = '';
  messages: { from: string; text: string }[] = [];
  isLoading = false;
  jobs: any[] = [];
  private sessionId!: string;

  constructor(
    private auth: AuthService,
    private chatService: ChatService,
    private cdr: ChangeDetectorRef
  ) {
    this.sessionId = this.getOrCreateSessionId();
  }

  ngOnInit(): void {
    this.loadJobs();
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

  // In hr.component.ts - update the loadJobs method

loadJobs(): void {
  console.log('Loading jobs...'); // Add debug log
  this.chatService.getJobs().subscribe({
    next: (res: any) => {
      console.log('Raw jobs response:', res); // Debug log
      
      // Handle different response formats
      let jobsArray = [];
      if (res.jobs && Array.isArray(res.jobs)) {
        jobsArray = res.jobs;
      } else if (Array.isArray(res)) {
        jobsArray = res;
      } else if (res.data && Array.isArray(res.data)) {
        jobsArray = res.data;
      } else {
        console.warn('Unexpected jobs response format:', res);
        jobsArray = [];
      }
      
      this.jobs = jobsArray.map((j: any) => {
        // Handle both camelCase and snake_case field names
        let skills: string[] = [];
        const rs = j.required_skills || j.requiredSkills;
        
        if (Array.isArray(rs)) {
          skills = rs;
        } else if (typeof rs === 'string') {
          try { 
            skills = JSON.parse(rs); 
          } catch(e) { 
            skills = []; 
          }
        }
        
        return {
          id: j.id,
          title: j.job_title || j.title || 'Untitled', // Handle both formats
          location: j.location || 'N/A',
          exp: j.experience_years || j.experienceYears ? `${j.experience_years || j.experienceYears} yrs` : 'N/A',
          skills: skills,
          positions: j.number_of_positions || j.numberOfPositions || 1,
        };
      });
      
      console.log('Processed jobs:', this.jobs); // Debug log
      this.cdr.detectChanges();
    },
    error: (err: any) => {
      console.error('Failed to load jobs:', err);
      // Show error in UI
      this.messages.push({ 
        from: 'bot', 
        text: '❌ Failed to load jobs. Please refresh the page.' 
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

    this.chatService.send(input, 'hr', this.sessionId).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.messages.push({ from: 'bot', text: res.reply || 'Done.' });
        const replyLower = (res.reply || '').toLowerCase();
        if (
          replyLower.includes('created') ||
          replyLower.includes('success') ||
          replyLower.includes('job id')
        ) {
          this.loadJobs();
        }
      },
      error: () => {
        this.isLoading = false;
        this.messages.push({ from: 'bot', text: '❌ Something went wrong. Please try again.' });
      },
    });
  }

  logout(): void {
    this.auth.logout();
  }
}