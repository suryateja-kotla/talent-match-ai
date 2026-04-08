import { CommonModule } from '@angular/common';
import { Component, Input, OnInit, ChangeDetectorRef } from '@angular/core';
import { ChatService } from '../../../services/chat.sevice'; // Adjust path if needed

@Component({
  selector: 'app-hr-jobs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hr-jobs.component.html',
  styleUrl: './hr-jobs.component.scss',
})
export class HrJobsComponent implements OnInit {
  // We keep this as an Input so we can still pass data manually if needed,
  // but it will now also manage its own state.
  @Input() jobs: any[] = [];
  isLoading = false;

  constructor(
    private chatService: ChatService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.fetchJobsFromDB();
  }

  // Public method so the HR/User parent can trigger a reload
  public refresh(): void {
    this.fetchJobsFromDB();
  }

  private fetchJobsFromDB(): void {
    this.isLoading = true;
    this.chatService.getJobs().subscribe({
      next: (res: any) => {
        let jobsArray = [];
        if (res.jobs && Array.isArray(res.jobs)) {
          jobsArray = res.jobs;
        } else if (Array.isArray(res)) {
          jobsArray = res;
        } else if (res.data && Array.isArray(res.data)) {
          jobsArray = res.data;
        }

        this.jobs = jobsArray.map((j: any) => {
          let skills: string[] = [];
          const rs = j.required_skills || j.requiredSkills;

          if (Array.isArray(rs)) {
            skills = rs;
          } else if (typeof rs === 'string') {
            try {
              skills = JSON.parse(rs);
            } catch (e) {
              skills = [];
            }
          }

          return {
            id: j.id,
            title: j.job_title || j.title || 'Untitled',
            location: j.location || 'N/A',
            exp:
              j.experience_years || j.experienceYears
                ? `${j.experience_years || j.experienceYears} yrs`
                : 'N/A',
            skills: skills,
            positions: j.number_of_positions || j.numberOfPositions || 1,
          };
        });

        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        console.error('Failed to load jobs:', err);
        this.isLoading = false;
      },
    });
  }
}
