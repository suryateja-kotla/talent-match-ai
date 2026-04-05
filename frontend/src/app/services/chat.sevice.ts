import { Injectable } from '@angular/core';

import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

export interface ChatResponse {
  reply: string;
}
export interface ResumeResponse {
  success: boolean;
  candidate_id: number;
  message: string;
  raw_response: string;
}
@Injectable({ providedIn: 'root' })
export class ChatService {
  private apiUrl = 'http://127.0.0.1:8000/api/route/chat';

  constructor(private http: HttpClient) {}
  send(
    message: string,
    userRole: string,
    sessionId: string,
    candidateId?: number | null, // 🔥 ADD THIS
  ) {
    return this.http.post<ChatResponse>(this.apiUrl, {
      message,
      user_role: userRole,
      session_id: sessionId,
      candidate_id: candidateId, // 🔥 SEND TO BACKEND
    });
  }
  uploadResume(file: File, sessionId: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId); // 🔥 ADD THIS

    return this.http.post<ResumeResponse>(
      'http://127.0.0.1:8000/resume/upload-and-parse',
      formData,
    );
  }
}
