// 2-bit binary adder
module adder_2bit(
    input wire [1:0] a,
    input wire [1:0] b,
    output wire [1:0] sum,
    output wire carry_out
);
    wire [2:0] result;
    
    assign result = a + b;
    assign sum = result[1:0];
    assign carry_out = result[2];
    
endmodule

