org   0x0000
BITS 16
CPU 8086

; d 18A6:56B0
section .newdata start=0x56B0
orig_timer_counter: dw 0
game_timer_counter: dw 0


; NOTES
; Game does about 21ms(48Hz) delay when unloaded (30-35Hz is 33-29ms)
; but might have taken longer with the drawing.. 
; we could try 35Hz or 29 ms
; or 10 cycles

; 0xa should be 10ms
; 2.746271935847088
; we should get 3.7
; should have been dx *1024 / 2.746271935847088*1024

; TODO:
; to try, xchg ax,dx then shift by 2
; save remaining, add onto next time!
; wait for change first?
; nah, just make sure it's AT LEAST.. so we need to round up

; important delays:
; one thing to keep in mind, we might not be taking into account rendering time
; 0x258 / 600 ;; intro 1Hz
; 0x1c / 28 ;; going up 35hz
; 0x28 / 40 ;; going down 25hz

; 18.2065 Hz is  54.925438716941752ms


; 0x10 bytes
section .delay_replace start=0x2e9
                mov     bx, sp
                mov     dx, ss:[bx+4]
                or      dx, dx
                jz      short locret_FD5_306
                call    do_delay
locret_FD5_306:                        
                retf    2


section .better_delay_impl start=0x660

do_delay:

    push ds

    mov ax, 0xDEAD
    mov ds, ax

    ;mov ax, dx
    xchg ax, dx
    xor dx, dx
    mov bx, 0x400 ;; mult 1024
    mul bx
    mov bx, 0xAFC ;; divide 2.746271935847088 * 1024
    div bx

    add ax, [ds:game_timer_counter]

delay_loop:
    cmp word [ds:game_timer_counter], ax
    jb      delay_loop

    pop ds
    retn