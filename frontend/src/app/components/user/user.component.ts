import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ChatbotComponent } from './chatbot/chatbot.component';
import { ApplicationsComponent } from './applications/applications.component';
import { JobMatchesComponent } from './job-matches/job-matches.component';
import { AuthService } from '../../services/auth.service';
import { JobService } from '../../services/job.service';
import { HrJobsComponent } from '../hr/hr-jobs/hr-jobs.component';

@Component({
  selector: 'app-user',
  standalone: true,
  imports: [
    CommonModule,
    ChatbotComponent,
    ApplicationsComponent,
    JobMatchesComponent,
    HrJobsComponent,
  ],
  templateUrl: './user.component.html',
  styleUrls: ['./user.component.scss'],
})
export class UserComponent {
  username: string = '';
  showMobileChat: boolean = false;

  jobs: any[] = [];
  applications: any[] = [];

  constructor(
    private router: Router,
    private authService: AuthService,
    private jobService: JobService,
  ) {}
  ngOnInit() {
    const user = this.authService.getCurrentUser();
    if (user) {
      this.username = user.username;
    } else {
      this.router.navigate(['/']);
    }
  }

  currentCandidateId = Number(localStorage.getItem('candidate_id'));

  onResumeParsed(data: any) {
    this.currentCandidateId = data.candidate_id;
  }
  // 🔐 Logout
  logout() {
    localStorage.removeItem('currentUser');
    sessionStorage.removeItem('currentUser');
    this.router.navigate(['/']);
  }
  toggleChat() {
    this.showMobileChat = !this.showMobileChat;
  }
}
