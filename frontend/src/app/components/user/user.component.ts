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
    HrJobsComponent
  ],
  templateUrl: './user.component.html',
  styleUrls: ['./user.component.scss'],
})
export class UserComponent {
  username: string = '';
  showMobileChat: boolean = false;
  // 🔥 Mock data for now (will replace later with API)
  jobs: any[] = [];
  applications: any[] = [];

  constructor(
    private router: Router,
    private authService: AuthService,
    private jobService: JobService,
  ) {}
  ngOnInit() {
    // Fetch the real user data from storage via the service
    const user = this.authService.getCurrentUser();
    if (user) {
      this.username = user.username;
    } else {
      // Security: If no user is found in storage, kick them back to login
      this.router.navigate(['/']);
    }
    // this.loadUser();
  }
  // Inside UserComponent.ts
currentCandidateId = Number(localStorage.getItem('candidate_id'));

// When the chatbot or resume upload returns an ID:
onResumeParsed(data: any) {
  this.currentCandidateId = data.candidate_id; 
  // This update will now automatically trigger the 'set candidateId' in the child!
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
