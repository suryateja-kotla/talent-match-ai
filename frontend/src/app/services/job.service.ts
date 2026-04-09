import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class JobService {
  private baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  getJobs(): Observable<any> {
    return this.http.get(`${this.baseUrl}/jobs`);
  }

  getApplications(candidateId: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/applications/${candidateId}`);
  }
  private refreshApplications = new Subject<void>();
  refreshApplications$ = this.refreshApplications.asObservable();

  triggerRefresh() {
    this.refreshApplications.next();
  }
}
