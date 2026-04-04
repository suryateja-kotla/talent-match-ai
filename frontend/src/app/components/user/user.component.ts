import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ChatbotComponent } from './chatbot/chatbot.component';
import { ApplicationsComponent } from './applications/applications.component';
import { JobMatchesComponent } from './job-matches/job-matches.component';

@Component({
  selector: 'app-user',
  standalone: true,
  imports: [CommonModule,ChatbotComponent,ApplicationsComponent,JobMatchesComponent],
  templateUrl: './user.component.html',
  styleUrls: ['./user.component.scss']
})
export class UserComponent {
   username: string = 'User1';

  // 🔥 Mock data for now (will replace later with API)
  jobs: any[] = [];
  applications: any[] = [];

  constructor(private router: Router) {}

  // 🔐 Logout
  logout() {
    localStorage.removeItem('currentUser');
    sessionStorage.removeItem('currentUser');
    this.router.navigate(['/']);
  }

}