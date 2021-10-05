org   0x0000

BITS 16
CPU 8086

section   .text

nop
nop
nop
retn

; TODO
; DONE: replace init
; DONE: replace cleanup
; add a delay to gameloop
; 65536 / 0x14


freq_divider:  equ   65536/20 ;  0xCCD

; d 18A6:56B0
section .newdata start=0x56B0

orig_timer_counter: dw 0
game_timer_counter: dw 0






section .seg7overrideset start=0x9a
; 8 bytes
; bp 16BC:9a
call s_set_timer_int_73EF
nop
nop
nop
nop
nop
nop
nop
nop


section .seg7overriderestore start=0xf4
;; 11 bytes
call s_restore_timer_7425
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop
nop





section .seg7timer start=0x1da0

; bp 16bc:1da0


s_timer_interrupt_70FF:
                pushf
                cli
                push ds
                push ax

                mov ax, 0xDEAD ; dseg
                mov ds, ax

                inc     word [ds:game_timer_counter]
                inc     word [ds:orig_timer_counter]

                cmp     word [ds:orig_timer_counter], 14h 
                jb      short loc_73AE

                mov     word [ds:orig_timer_counter], 0 
                sti
                pop     ax
                pop     ds
                call    far [cs:int_timer_orig]
                jmp     short loc_73B7

                        
loc_73AE:       mov     al, 20h 
                out     20h, al         

                pop ax
                pop ds
                popf

                     
loc_73B7:        sti
                iret

int_timer_orig dd 0



s_set_timer_int_73EF:        

                push ds
                push ax

                mov ax, 0xDEAD ; dseg
                mov ds, ax

                cli
                
                mov     word [ds:game_timer_counter], 0
                mov     word [ds:orig_timer_counter], 0

                mov     ax, 3508h
                int     21h             ; DOS - 2+ - GET INTERRUPT VECTOR
                                        ; AL = interrupt number
                                        ; Return: ES:BX = value of interrupt vector
                mov     word  [cs:int_timer_orig], bx
                mov     word  [cs:int_timer_orig+2], es

                push    ds
                push    cs
                pop     ds
                mov     dx,  s_timer_interrupt_70FF
                mov     ax, 2508h
                int     21h             ; DOS - SET INTERRUPT VECTOR
                                        ; AL = interrupt number
                                        ; DS:DX = new vector to be used for specified interrupt
                pop     ds

                mov     al, 36h ; '6'
                out     43h, al         ; Timer 8253-5 (AT: 8254.2).

                mov     ax, freq_divider
                out     40h, al         ; Timer 8253-5 (AT: 8254.2).
                xchg    ah, al
                out     40h, al         ; Timer 8253-5 (AT: 8254.2).

                sti

                pop ax
                pop ds
                retn


s_restore_timer_7425:

                push ds
                push ax

                mov ax, 0xDEAD ; dseg
                mov ds, ax

                cli

                mov     al, 36h ; '6'
                out     43h, al         ; Timer 8253-5 (AT: 8254.2).

                mov     ax, 0
                out     40h, al         ; Timer 8253-5 (AT: 8254.2).
                xchg    ah, al
                out     40h, al         ; Timer 8253-5 (AT: 8254.2).



                push    ds
                mov     dx, word  [cs:int_timer_orig]
                mov     ds, word  [cs:int_timer_orig+2]
                mov     ah, 25h 
                mov     al, 8
                int     21h             ; DOS - SET INTERRUPT VECTOR
                                        ; AL = interrupt number
                                        ; DS:DX = new vector to be used for specified interrupt
                pop     ds

                sti

                pop ax
                pop ds
                retn



