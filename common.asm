
wait_for_vertical_retrace:
    cli
    push dx
    push ax

    mov     dx, 3DAh        ; Video status bits:
                            ; 3: 1=vertical sync pulse is occurring.

; wait_for_cleared_bit:                             
;     in      al, dx          
;     and     al, 8
;     jnz     wait_for_cleared_bit

wait_for_set_bit:                               
    in      al, dx         
    and     al, 8
    jz      wait_for_set_bit

    pop ax
    pop dx
    sti
    retn
    

delay_init:
    mov  word [ds:game_timer_counter], 0
    retn


do_delay:

        push ds
        push ax

        mov ax, 0xDEAD ; dseg
        mov ds, ax

        delay_loop:
        cmp word [ds:game_timer_counter], bx
        jb      delay_loop

        mov  word [ds:game_timer_counter], 0

        pop ax
        pop ds

        retn
