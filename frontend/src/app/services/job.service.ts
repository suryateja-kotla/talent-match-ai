import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class JobService {
  private apiUrl = 'your-gcp-backend-url/api/jobs'; // Adjust to your GCP backend

  constructor(private http: HttpClient) {}

  // Fetch all active jobs from Cloud SQL
  getJobs(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }
}