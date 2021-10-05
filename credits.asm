org   0x0000

BITS 16
CPU 8086


; d 18A6:56B0
section .newdata start=0x56B0

orig_timer_counter: dw 0
game_timer_counter: dw 0


absolute 0x1d04 
s_game_update_0_1D04: ;ret


; 5 bytes
section .call_intro_pre start=0x396a
    call intro_pre
    nop
    nop

; 3 bytes
section .call_intro_start start=0x396f
    call intro_start
    nop
    nop
    nop

; 4 bytes
section .call_intro_end start=0x399c
    call intro_end
    nop
    nop
    nop
    nop



; 3 bytes
section .call_credits_start start=0x3ecb
    call credits_start
    nop
    nop
    nop

; 4 bytes
section .call_credits_end start=0x3f71
    call credits_end
    nop
    nop
    nop
    nop




section .credits_timing start=0x4210

;
intro_pre:
    call near delay_init
    ;; original instr
    mov     word  [bp-0Ch], 1
    retn

intro_start:
    call near vsync_wait

    ;; original instr
    mov     ax, [bp-0Ch]
    retn

intro_end:
    push bx
    mov bx, 0xBC
    call near do_delay
    pop bx

    ;; original instr
    cmp     word  [bp-0Ch], 0Ch
    retn


credits_start:
    call near vsync_wait

    ;; original instr
    mov     ax, 68h ; 'h'
    retn

credits_end:
    push bx
    mov bx, 0x9
    call near do_delay
    pop bx

    ;; original instr
    cmp     word  [bp-0Ah], 1
    retn



vsync_wait:
                cli
                push dx
                push ax

                mov     dx, 3DAh        ; Video status bits:
                                        ; 3: 1=vertical sync pulse is occurring.

            wait_until_no_vsync:                             
                in      al, dx          
                and     al, 8
                jnz     wait_until_no_vsync


            wait_until_vsync:                               
                in      al, dx         
                and     al, 8
                jz      wait_until_vsync

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
