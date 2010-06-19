
      subroutine complex_default(r1,r2,r3)
          implicit none
          complex, intent(in) :: r1
          complex, intent(inout) :: r2
          complex, intent(out) :: r3
          r2 = 2*r1
          r3 = 2*r2 - 5*r1
      end subroutine
      subroutine complex_x_len(r10,r11,r12,r13,r14,r15)
          implicit none
          complex*8, intent(in) :: r10
          complex*8, intent(inout) :: r11
          complex*8, intent(out) :: r12
          complex*16, intent(in) :: r13
          complex*16, intent(inout) :: r14
          complex*16, intent(out) :: r15
          r11 = 2*r10
          r12 = 3*r11 - 5*r10
          r14 = conjg(r13)
          r15 = r14 - r13
      end subroutine
      subroutine complex_kind_x(r7,r8,r9,r10,r11,r12)
          implicit none
          complex(kind=4), intent(in) :: r7
          complex(kind=4), intent(inout) :: r8
          complex(kind=4), intent(out) :: r9
          complex(kind=8), intent(in) :: r10
          complex(kind=8), intent(inout) :: r11
          complex(kind=8), intent(out) :: r12
          r8 = r7
          r9 = r8 * r7 / 2.0
          r11 = r10**3
          r12 = r11 - conjg(r10)
      end subroutine
      ! subroutine complex_kind_call(r1,r2,r3,r4,r5,r6)
          ! implicit none
          ! complex(kind=kind((0.0,0.0))), intent(in) :: r1
          ! complex(kind=kind((0.0,0.0))), intent(inout) :: r2
          ! complex(kind=kind((0.0,0.0))), intent(out) :: r3
          ! complex(kind=kind((0.0D0,0.0D0))), intent(in) :: r4
          ! complex(kind=kind((0.0D0,0.0D0))), intent(inout) :: r5
          ! complex(kind=kind((0.0D0,0.0D0))), intent(out) :: r6
      ! end subroutine
      ! subroutine complex_srk_call(r1,r2,r3,r4,r5,r6,r7,r8,r9)
          ! implicit none
          ! complex(kind=selected_real_kind(1)), intent(in) :: r1
          ! complex(kind=selected_real_kind(1)), intent(inout) :: r2
          ! complex(kind=selected_real_kind(1)), intent(out) :: r3
          ! complex(kind=selected_real_kind(7)), intent(in) :: r4
          ! complex(kind=selected_real_kind(7)), intent(inout) :: r5
          ! complex(kind=selected_real_kind(7)), intent(out) :: r6
          ! complex(kind=selected_real_kind(14)), intent(in) :: r7
          ! complex(kind=selected_real_kind(14)), intent(inout) :: r8
          ! complex(kind=selected_real_kind(14)), intent(out) :: r9
      ! end subroutine
