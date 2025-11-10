`timescale 1ns / 1ps

module turnstile_controller (
    input  wire clk,
    input  wire rst,
    input  wire coin,
    input  wire push,
    output reg  locked,
    output reg  alarm
);
    localparam S_LOCKED   = 1'b0;
    localparam S_UNLOCKED = 1'b1;

    reg state;
    reg next_state;

    always @(posedge clk) begin
        if (rst) begin
            state <= S_LOCKED;
        end else begin
            state <= next_state;
        end
    end

    always @(*) begin
        alarm = 1'b0;
        locked = (state == S_LOCKED);
        next_state = state;

        case (state)
            S_LOCKED: begin
                if (coin) begin
                    next_state = S_UNLOCKED;
                    locked = 1'b0;
                end else if (push) begin
                    next_state = S_LOCKED;
                    locked = 1'b1;
                    alarm = 1'b1;
                end
            end
            S_UNLOCKED: begin
                locked = 1'b0;
                if (push) begin
                    next_state = S_LOCKED;
                    locked = 1'b1;
                end
            end
            default: begin
                next_state = S_LOCKED;
                locked = 1'b1;
            end
        endcase
    end
endmodule

