import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatResponse {
  reply: string;
}

export interface JobsResponse {
  jobs: any[];
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  private baseUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  send(message: string, userRole: string, sessionId: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.baseUrl}/api/route/chat`, {
      message,
      user_role: userRole,
      session_id: sessionId,
    });
  }

  getJobs(): Observable<JobsResponse> {
    return this.http.get<JobsResponse>(`${this.baseUrl}/api/jobs`);
  }

  uploadResume(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.baseUrl}/resume/upload-and-parse`, formData);
  }
}