import { CommonModule } from '@angular/common';
import {
  Component,
  Input,
  OnInit,
  ChangeDetectorRef,
  ViewChild,
  ElementRef,
} from '@angular/core';
import { ChatService } from '../../../services/chat.sevice'; // Adjust path if needed

declare var bootstrap: any;

@Component({
  selector: 'app-hr-jobs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hr-jobs.component.html',
  styleUrl: './hr-jobs.component.scss',
})
export class HrJobsComponent implements OnInit {
  @Input() jobs: any[] = [];
  isLoading = false;
  selectedJob: any = null;
  @ViewChild('detailModal') modalElement!: ElementRef;

  constructor(
    private chatService: ChatService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.fetchJobsFromDB();
  }
  openJobDetails(job: any): void {
    this.selectedJob = job;
    this.cdr.detectChanges(); 

    const element = this.modalElement.nativeElement;
    document.body.appendChild(element);

   
    let modalInstance = bootstrap.Modal.getInstance(element);
    if (!modalInstance) {
      modalInstance = new bootstrap.Modal(element, {
        backdrop: true, 
        keyboard: true,
      });
    }

    modalInstance.show();
  }
  closeModal(): void {
    const element = this.modalElement.nativeElement;

    const modalInstance = bootstrap.Modal.getInstance(element);
    modalInstance?.hide();

   
    setTimeout(() => {
      document.body.removeChild(element);
    }, 300);
  }

  
  public refresh(): void {
    this.fetchJobsFromDB();
  }

  private fetchJobsFromDB(): void {
    this.isLoading = true;
    this.chatService.getJobs().subscribe({
      next: (res: any) => {
        console.log('FULL API RESPONSE:', res);
        let jobsArray = [];
        if (res.jobs && Array.isArray(res.jobs)) {
          jobsArray = res.jobs;
        } else if (Array.isArray(res)) {
          jobsArray = res;
        } else if (res.data && Array.isArray(res.data)) {
          jobsArray = res.data;
        }

        this.jobs = jobsArray.map((j: any) => {
          console.log('EACH JOB:', j);
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
            description: j.job_description || 'No description available',
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
