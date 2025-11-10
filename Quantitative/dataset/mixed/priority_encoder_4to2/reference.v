`timescale 1ns / 1ps

module priority_encoder_4to2 (
    input  wire [3:0] req,
    output wire [1:0] code,
    output wire       valid
);
    assign valid = |req;
    assign code =
        req[3] ? 2'b11 :
        req[2] ? 2'b10 :
        req[1] ? 2'b01 :
        req[0] ? 2'b00 : 2'b00;
endmodule

