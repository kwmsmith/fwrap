      subroutine explicit_shape(n1, n2, ain, aout, ainout, ano)
        implicit none
        integer, intent(in) :: n1, n2
        logical, dimension(n1, n2), intent(in) :: ain
        logical, dimension(n1, n2), intent(out) :: aout
        logical, dimension(n1, n2), intent(inout) :: ainout
        logical, dimension(n1, n2) :: ano

        aout = ain
        ano = ainout
        where(ain)
            ainout = .false.
        endwhere
      end subroutine explicit_shape

      subroutine assumed_shape(ain, aout, ainout, ano)
        implicit none
        logical, dimension(:, :), intent(in) :: ain
        logical, dimension(:, :), intent(out) :: aout
        logical, dimension(:, :), intent(inout) :: ainout
        logical, dimension(:, :) :: ano

        aout = ain
        ano = ainout
        where(ain)
            ainout = .false.
        endwhere
      end subroutine assumed_shape

      subroutine assumed_size(n1, n2, ain, aout, ainout, ano)
        implicit none
        integer, intent(in) :: n1, n2
        logical, dimension(n1, *), intent(in) :: ain
        logical, dimension(n1, *), intent(out) :: aout
        logical, dimension(n1, *), intent(inout) :: ainout
        logical, dimension(n1, *) :: ano

        aout(:,1:n2) = ain(:,1:n2)
        ano(:,1:n2) = ainout(:,1:n2)
        where(ain(:,1:n2))
            ainout(:,1:n2) = .false.
        endwhere
      end subroutine assumed_size
