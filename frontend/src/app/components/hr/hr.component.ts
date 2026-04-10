import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { HrChatComponent } from './hr-chat/hr-chat.component';
import { HrJobsComponent } from './hr-jobs/hr-jobs.component';
import { ViewChild } from '@angular/core';

@Component({
  selector: 'app-hr',
  standalone: true,
  imports: [CommonModule, FormsModule, HrChatComponent, HrJobsComponent],
  templateUrl: './hr.component.html',
  styleUrl: './hr.component.scss',
})
export class HrComponent implements OnInit {
  showMobileChat: boolean = false;

  @ViewChild(HrJobsComponent) hrJobs!: HrJobsComponent;

  constructor(private auth: AuthService) {}

  ngOnInit(): void {}

  logout(): void {
    this.auth.logout();
  }

  toggleChat() {
    this.showMobileChat = !this.showMobileChat;
  }

  handleJobCreated() {
    if (this.hrJobs) {
      this.hrJobs.refresh();
    }
  }
}
