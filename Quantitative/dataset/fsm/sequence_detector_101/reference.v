`timescale 1ns / 1ps

module sequence_detector_101 (
    input  wire clk,
    input  wire rst,
    input  wire in_bit,
    output reg  detected
);
    localparam S0 = 2'b00;
    localparam S1 = 2'b01;
    localparam S2 = 2'b10;

    reg [1:0] state;
    reg [1:0] next_state;

    always @(posedge clk) begin
        if (rst) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    always @(*) begin
        detected = 1'b0;
        case (state)
            S0: begin
                next_state = in_bit ? S1 : S0;
            end
            S1: begin
                next_state = in_bit ? S1 : S2;
            end
            S2: begin
                if (in_bit) begin
                    detected = 1'b1;
                    next_state = S1;
                end else begin
                    next_state = S0;
                end
            end
            default: begin
                next_state = S0;
            end
        endcase
    end
endmodule

