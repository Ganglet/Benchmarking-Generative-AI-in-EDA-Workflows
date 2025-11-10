`timescale 1ns / 1ps

module simple_alu_4bit (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire [1:0] op,
    output reg  [3:0] result,
    output reg        carry_out,
    output reg        zero
);
    always @(*) begin
        case (op)
            2'b00: {carry_out, result} = a + b;
            2'b01: {carry_out, result} = a - b;
            2'b10: begin
                result = a & b;
                carry_out = 1'b0;
            end
            2'b11: begin
                result = a ^ b;
                carry_out = 1'b0;
            end
            default: begin
                result = 4'h0;
                carry_out = 1'b0;
            end
        endcase
        zero = (result == 4'h0);
    end
endmodule

