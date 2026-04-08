import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HrChatComponent } from './hr-chat.component';

describe('HrChatComponent', () => {
  let component: HrChatComponent;
  let fixture: ComponentFixture<HrChatComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HrChatComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HrChatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
