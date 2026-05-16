package main

import "fmt"

type Knot struct {
	Name string         `json:"name"`
	Rank int            `json:"rank"`
	Bag  map[string]any `json:"bag"`
	Next *Knot          `json:"next,omitempty"`
}

type Drift struct {
	Left  Packet
	Right Packet
	Knot  Knot
	Trail []Hop
}

func knotSeed(name string, rank int) Knot {
	return Knot{Name: name, Rank: rank, Bag: map[string]any{"seed": name, "rank": rank}}
}

func knotJoin(a Knot, b Knot) Knot {
	a.Next = &b
	a.Bag["joined"] = b.Name
	return a
}

func packetMark(p Packet, s Stamp) Packet {
	p.Marks = append(p.Marks, s)
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire[string(s)] = len(p.Marks)
	return p
}

func packetFork(p Packet, k Knot) Drift {
	q := p
	q.Wire = map[string]any{"fork": k.Name, "rank": k.Rank}
	return Drift{Left: p, Right: q, Knot: k, Trail: []Hop{{Name: "fork", Value: k.Name}}}
}

func driftFold(d Drift) Packet {
	p := d.Right
	p.Carry = &d.Left
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["folded"] = d.Knot.Name
	return p
}

func weave1(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_1"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w1-%d", n)))
	if g.OK {
		p.Wire["gate_1"] = g.TeamID + n + 1
	} else {
		p.Wire["gate_1"] = g.Reason
	}
	return p
}

func braid1(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-1-%d", len(p.Marks)), 1)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave1(p, d.Right.G, 1)
	return d
}

func weave2(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_2"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w2-%d", n)))
	if g.OK {
		p.Wire["gate_2"] = g.TeamID + n + 2
	} else {
		p.Wire["gate_2"] = g.Reason
	}
	return p
}

func braid2(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-2-%d", len(p.Marks)), 2)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave2(p, d.Right.G, 2)
	return d
}

func weave3(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_3"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w3-%d", n)))
	if g.OK {
		p.Wire["gate_3"] = g.TeamID + n + 3
	} else {
		p.Wire["gate_3"] = g.Reason
	}
	return p
}

func braid3(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-3-%d", len(p.Marks)), 3)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave3(p, d.Right.G, 3)
	return d
}

func weave4(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_4"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w4-%d", n)))
	if g.OK {
		p.Wire["gate_4"] = g.TeamID + n + 4
	} else {
		p.Wire["gate_4"] = g.Reason
	}
	return p
}

func braid4(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-4-%d", len(p.Marks)), 4)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave4(p, d.Right.G, 4)
	return d
}

func weave5(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_5"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w5-%d", n)))
	if g.OK {
		p.Wire["gate_5"] = g.TeamID + n + 5
	} else {
		p.Wire["gate_5"] = g.Reason
	}
	return p
}

func braid5(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-5-%d", len(p.Marks)), 5)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave5(p, d.Right.G, 5)
	return d
}

func weave6(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_6"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w6-%d", n)))
	if g.OK {
		p.Wire["gate_6"] = g.TeamID + n + 6
	} else {
		p.Wire["gate_6"] = g.Reason
	}
	return p
}

func braid6(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-6-%d", len(p.Marks)), 6)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave6(p, d.Right.G, 6)
	return d
}

func weave7(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_7"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w7-%d", n)))
	if g.OK {
		p.Wire["gate_7"] = g.TeamID + n + 7
	} else {
		p.Wire["gate_7"] = g.Reason
	}
	return p
}

func braid7(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-7-%d", len(p.Marks)), 7)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave7(p, d.Right.G, 7)
	return d
}

func weave8(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_8"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w8-%d", n)))
	if g.OK {
		p.Wire["gate_8"] = g.TeamID + n + 8
	} else {
		p.Wire["gate_8"] = g.Reason
	}
	return p
}

func braid8(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-8-%d", len(p.Marks)), 8)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave8(p, d.Right.G, 8)
	return d
}

func weave9(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_9"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w9-%d", n)))
	if g.OK {
		p.Wire["gate_9"] = g.TeamID + n + 9
	} else {
		p.Wire["gate_9"] = g.Reason
	}
	return p
}

func braid9(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-9-%d", len(p.Marks)), 9)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave9(p, d.Right.G, 9)
	return d
}

func weave10(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_10"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w10-%d", n)))
	if g.OK {
		p.Wire["gate_10"] = g.TeamID + n + 10
	} else {
		p.Wire["gate_10"] = g.Reason
	}
	return p
}

func braid10(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-10-%d", len(p.Marks)), 10)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave10(p, d.Right.G, 10)
	return d
}

func weave11(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_11"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w11-%d", n)))
	if g.OK {
		p.Wire["gate_11"] = g.TeamID + n + 11
	} else {
		p.Wire["gate_11"] = g.Reason
	}
	return p
}

func braid11(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-11-%d", len(p.Marks)), 11)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave11(p, d.Right.G, 11)
	return d
}

func weave12(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_12"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w12-%d", n)))
	if g.OK {
		p.Wire["gate_12"] = g.TeamID + n + 12
	} else {
		p.Wire["gate_12"] = g.Reason
	}
	return p
}

func braid12(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-12-%d", len(p.Marks)), 12)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave12(p, d.Right.G, 12)
	return d
}

func weave13(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_13"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w13-%d", n)))
	if g.OK {
		p.Wire["gate_13"] = g.TeamID + n + 13
	} else {
		p.Wire["gate_13"] = g.Reason
	}
	return p
}

func braid13(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-13-%d", len(p.Marks)), 13)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave13(p, d.Right.G, 13)
	return d
}

func weave14(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_14"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w14-%d", n)))
	if g.OK {
		p.Wire["gate_14"] = g.TeamID + n + 14
	} else {
		p.Wire["gate_14"] = g.Reason
	}
	return p
}

func braid14(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-14-%d", len(p.Marks)), 14)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave14(p, d.Right.G, 14)
	return d
}

func weave15(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_15"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w15-%d", n)))
	if g.OK {
		p.Wire["gate_15"] = g.TeamID + n + 15
	} else {
		p.Wire["gate_15"] = g.Reason
	}
	return p
}

func braid15(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-15-%d", len(p.Marks)), 15)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave15(p, d.Right.G, 15)
	return d
}

func weave16(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_16"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w16-%d", n)))
	if g.OK {
		p.Wire["gate_16"] = g.TeamID + n + 16
	} else {
		p.Wire["gate_16"] = g.Reason
	}
	return p
}

func braid16(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-16-%d", len(p.Marks)), 16)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave16(p, d.Right.G, 16)
	return d
}

func weave17(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_17"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w17-%d", n)))
	if g.OK {
		p.Wire["gate_17"] = g.TeamID + n + 17
	} else {
		p.Wire["gate_17"] = g.Reason
	}
	return p
}

func braid17(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-17-%d", len(p.Marks)), 17)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave17(p, d.Right.G, 17)
	return d
}

func weave18(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_18"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w18-%d", n)))
	if g.OK {
		p.Wire["gate_18"] = g.TeamID + n + 18
	} else {
		p.Wire["gate_18"] = g.Reason
	}
	return p
}

func braid18(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-18-%d", len(p.Marks)), 18)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave18(p, d.Right.G, 18)
	return d
}

func weave19(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_19"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w19-%d", n)))
	if g.OK {
		p.Wire["gate_19"] = g.TeamID + n + 19
	} else {
		p.Wire["gate_19"] = g.Reason
	}
	return p
}

func braid19(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-19-%d", len(p.Marks)), 19)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave19(p, d.Right.G, 19)
	return d
}

func weave20(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_20"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w20-%d", n)))
	if g.OK {
		p.Wire["gate_20"] = g.TeamID + n + 20
	} else {
		p.Wire["gate_20"] = g.Reason
	}
	return p
}

func braid20(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-20-%d", len(p.Marks)), 20)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave20(p, d.Right.G, 20)
	return d
}

func weave21(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_21"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w21-%d", n)))
	if g.OK {
		p.Wire["gate_21"] = g.TeamID + n + 21
	} else {
		p.Wire["gate_21"] = g.Reason
	}
	return p
}

func braid21(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-21-%d", len(p.Marks)), 21)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave21(p, d.Right.G, 21)
	return d
}

func weave22(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_22"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w22-%d", n)))
	if g.OK {
		p.Wire["gate_22"] = g.TeamID + n + 22
	} else {
		p.Wire["gate_22"] = g.Reason
	}
	return p
}

func braid22(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-22-%d", len(p.Marks)), 22)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave22(p, d.Right.G, 22)
	return d
}

func weave23(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_23"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w23-%d", n)))
	if g.OK {
		p.Wire["gate_23"] = g.TeamID + n + 23
	} else {
		p.Wire["gate_23"] = g.Reason
	}
	return p
}

func braid23(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-23-%d", len(p.Marks)), 23)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave23(p, d.Right.G, 23)
	return d
}

func weave24(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_24"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w24-%d", n)))
	if g.OK {
		p.Wire["gate_24"] = g.TeamID + n + 24
	} else {
		p.Wire["gate_24"] = g.Reason
	}
	return p
}

func braid24(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-24-%d", len(p.Marks)), 24)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave24(p, d.Right.G, 24)
	return d
}

func weave25(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_25"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w25-%d", n)))
	if g.OK {
		p.Wire["gate_25"] = g.TeamID + n + 25
	} else {
		p.Wire["gate_25"] = g.Reason
	}
	return p
}

func braid25(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-25-%d", len(p.Marks)), 25)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave25(p, d.Right.G, 25)
	return d
}

func weave26(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_26"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w26-%d", n)))
	if g.OK {
		p.Wire["gate_26"] = g.TeamID + n + 26
	} else {
		p.Wire["gate_26"] = g.Reason
	}
	return p
}

func braid26(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-26-%d", len(p.Marks)), 26)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave26(p, d.Right.G, 26)
	return d
}

func weave27(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_27"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w27-%d", n)))
	if g.OK {
		p.Wire["gate_27"] = g.TeamID + n + 27
	} else {
		p.Wire["gate_27"] = g.Reason
	}
	return p
}

func braid27(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-27-%d", len(p.Marks)), 27)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave27(p, d.Right.G, 27)
	return d
}

func weave28(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_28"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w28-%d", n)))
	if g.OK {
		p.Wire["gate_28"] = g.TeamID + n + 28
	} else {
		p.Wire["gate_28"] = g.Reason
	}
	return p
}

func braid28(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-28-%d", len(p.Marks)), 28)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave28(p, d.Right.G, 28)
	return d
}

func weave29(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_29"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w29-%d", n)))
	if g.OK {
		p.Wire["gate_29"] = g.TeamID + n + 29
	} else {
		p.Wire["gate_29"] = g.Reason
	}
	return p
}

func braid29(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-29-%d", len(p.Marks)), 29)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave29(p, d.Right.G, 29)
	return d
}

func weave30(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_30"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w30-%d", n)))
	if g.OK {
		p.Wire["gate_30"] = g.TeamID + n + 30
	} else {
		p.Wire["gate_30"] = g.Reason
	}
	return p
}

func braid30(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-30-%d", len(p.Marks)), 30)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave30(p, d.Right.G, 30)
	return d
}

func weave31(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_31"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w31-%d", n)))
	if g.OK {
		p.Wire["gate_31"] = g.TeamID + n + 31
	} else {
		p.Wire["gate_31"] = g.Reason
	}
	return p
}

func braid31(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-31-%d", len(p.Marks)), 31)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave31(p, d.Right.G, 31)
	return d
}

func weave32(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_32"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w32-%d", n)))
	if g.OK {
		p.Wire["gate_32"] = g.TeamID + n + 32
	} else {
		p.Wire["gate_32"] = g.Reason
	}
	return p
}

func braid32(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-32-%d", len(p.Marks)), 32)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave32(p, d.Right.G, 32)
	return d
}

func weave33(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_33"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w33-%d", n)))
	if g.OK {
		p.Wire["gate_33"] = g.TeamID + n + 33
	} else {
		p.Wire["gate_33"] = g.Reason
	}
	return p
}

func braid33(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-33-%d", len(p.Marks)), 33)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave33(p, d.Right.G, 33)
	return d
}

func weave34(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_34"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w34-%d", n)))
	if g.OK {
		p.Wire["gate_34"] = g.TeamID + n + 34
	} else {
		p.Wire["gate_34"] = g.Reason
	}
	return p
}

func braid34(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-34-%d", len(p.Marks)), 34)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave34(p, d.Right.G, 34)
	return d
}

func weave35(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_35"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w35-%d", n)))
	if g.OK {
		p.Wire["gate_35"] = g.TeamID + n + 35
	} else {
		p.Wire["gate_35"] = g.Reason
	}
	return p
}

func braid35(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-35-%d", len(p.Marks)), 35)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave35(p, d.Right.G, 35)
	return d
}

func weave36(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_36"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w36-%d", n)))
	if g.OK {
		p.Wire["gate_36"] = g.TeamID + n + 36
	} else {
		p.Wire["gate_36"] = g.Reason
	}
	return p
}

func braid36(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-36-%d", len(p.Marks)), 36)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave36(p, d.Right.G, 36)
	return d
}

func weave37(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_37"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w37-%d", n)))
	if g.OK {
		p.Wire["gate_37"] = g.TeamID + n + 37
	} else {
		p.Wire["gate_37"] = g.Reason
	}
	return p
}

func braid37(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-37-%d", len(p.Marks)), 37)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave37(p, d.Right.G, 37)
	return d
}

func weave38(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_38"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w38-%d", n)))
	if g.OK {
		p.Wire["gate_38"] = g.TeamID + n + 38
	} else {
		p.Wire["gate_38"] = g.Reason
	}
	return p
}

func braid38(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-38-%d", len(p.Marks)), 38)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave38(p, d.Right.G, 38)
	return d
}

func weave39(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_39"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w39-%d", n)))
	if g.OK {
		p.Wire["gate_39"] = g.TeamID + n + 39
	} else {
		p.Wire["gate_39"] = g.Reason
	}
	return p
}

func braid39(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-39-%d", len(p.Marks)), 39)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave39(p, d.Right.G, 39)
	return d
}

func weave40(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_40"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w40-%d", n)))
	if g.OK {
		p.Wire["gate_40"] = g.TeamID + n + 40
	} else {
		p.Wire["gate_40"] = g.Reason
	}
	return p
}

func braid40(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-40-%d", len(p.Marks)), 40)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave40(p, d.Right.G, 40)
	return d
}

func weave41(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_41"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w41-%d", n)))
	if g.OK {
		p.Wire["gate_41"] = g.TeamID + n + 41
	} else {
		p.Wire["gate_41"] = g.Reason
	}
	return p
}

func braid41(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-41-%d", len(p.Marks)), 41)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave41(p, d.Right.G, 41)
	return d
}

func weave42(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_42"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w42-%d", n)))
	if g.OK {
		p.Wire["gate_42"] = g.TeamID + n + 42
	} else {
		p.Wire["gate_42"] = g.Reason
	}
	return p
}

func braid42(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-42-%d", len(p.Marks)), 42)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave42(p, d.Right.G, 42)
	return d
}

func weave43(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_43"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w43-%d", n)))
	if g.OK {
		p.Wire["gate_43"] = g.TeamID + n + 43
	} else {
		p.Wire["gate_43"] = g.Reason
	}
	return p
}

func braid43(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-43-%d", len(p.Marks)), 43)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave43(p, d.Right.G, 43)
	return d
}

func weave44(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_44"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w44-%d", n)))
	if g.OK {
		p.Wire["gate_44"] = g.TeamID + n + 44
	} else {
		p.Wire["gate_44"] = g.Reason
	}
	return p
}

func braid44(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-44-%d", len(p.Marks)), 44)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave44(p, d.Right.G, 44)
	return d
}

func weave45(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_45"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w45-%d", n)))
	if g.OK {
		p.Wire["gate_45"] = g.TeamID + n + 45
	} else {
		p.Wire["gate_45"] = g.Reason
	}
	return p
}

func braid45(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-45-%d", len(p.Marks)), 45)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave45(p, d.Right.G, 45)
	return d
}

func weave46(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_46"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w46-%d", n)))
	if g.OK {
		p.Wire["gate_46"] = g.TeamID + n + 46
	} else {
		p.Wire["gate_46"] = g.Reason
	}
	return p
}

func braid46(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-46-%d", len(p.Marks)), 46)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave46(p, d.Right.G, 46)
	return d
}

func weave47(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_47"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w47-%d", n)))
	if g.OK {
		p.Wire["gate_47"] = g.TeamID + n + 47
	} else {
		p.Wire["gate_47"] = g.Reason
	}
	return p
}

func braid47(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-47-%d", len(p.Marks)), 47)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave47(p, d.Right.G, 47)
	return d
}

func weave48(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_48"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w48-%d", n)))
	if g.OK {
		p.Wire["gate_48"] = g.TeamID + n + 48
	} else {
		p.Wire["gate_48"] = g.Reason
	}
	return p
}

func braid48(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-48-%d", len(p.Marks)), 48)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave48(p, d.Right.G, 48)
	return d
}

func weave49(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_49"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w49-%d", n)))
	if g.OK {
		p.Wire["gate_49"] = g.TeamID + n + 49
	} else {
		p.Wire["gate_49"] = g.Reason
	}
	return p
}

func braid49(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-49-%d", len(p.Marks)), 49)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave49(p, d.Right.G, 49)
	return d
}

func weave50(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_50"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w50-%d", n)))
	if g.OK {
		p.Wire["gate_50"] = g.TeamID + n + 50
	} else {
		p.Wire["gate_50"] = g.Reason
	}
	return p
}

func braid50(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-50-%d", len(p.Marks)), 50)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave50(p, d.Right.G, 50)
	return d
}

func weave51(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_51"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w51-%d", n)))
	if g.OK {
		p.Wire["gate_51"] = g.TeamID + n + 51
	} else {
		p.Wire["gate_51"] = g.Reason
	}
	return p
}

func braid51(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-51-%d", len(p.Marks)), 51)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave51(p, d.Right.G, 51)
	return d
}

func weave52(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_52"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w52-%d", n)))
	if g.OK {
		p.Wire["gate_52"] = g.TeamID + n + 52
	} else {
		p.Wire["gate_52"] = g.Reason
	}
	return p
}

func braid52(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-52-%d", len(p.Marks)), 52)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave52(p, d.Right.G, 52)
	return d
}

func weave53(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_53"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w53-%d", n)))
	if g.OK {
		p.Wire["gate_53"] = g.TeamID + n + 53
	} else {
		p.Wire["gate_53"] = g.Reason
	}
	return p
}

func braid53(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-53-%d", len(p.Marks)), 53)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave53(p, d.Right.G, 53)
	return d
}

func weave54(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_54"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w54-%d", n)))
	if g.OK {
		p.Wire["gate_54"] = g.TeamID + n + 54
	} else {
		p.Wire["gate_54"] = g.Reason
	}
	return p
}

func braid54(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-54-%d", len(p.Marks)), 54)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave54(p, d.Right.G, 54)
	return d
}

func weave55(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_55"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w55-%d", n)))
	if g.OK {
		p.Wire["gate_55"] = g.TeamID + n + 55
	} else {
		p.Wire["gate_55"] = g.Reason
	}
	return p
}

func braid55(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-55-%d", len(p.Marks)), 55)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave55(p, d.Right.G, 55)
	return d
}

func weave56(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_56"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w56-%d", n)))
	if g.OK {
		p.Wire["gate_56"] = g.TeamID + n + 56
	} else {
		p.Wire["gate_56"] = g.Reason
	}
	return p
}

func braid56(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-56-%d", len(p.Marks)), 56)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave56(p, d.Right.G, 56)
	return d
}

func weave57(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_57"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w57-%d", n)))
	if g.OK {
		p.Wire["gate_57"] = g.TeamID + n + 57
	} else {
		p.Wire["gate_57"] = g.Reason
	}
	return p
}

func braid57(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-57-%d", len(p.Marks)), 57)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave57(p, d.Right.G, 57)
	return d
}

func weave58(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_58"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w58-%d", n)))
	if g.OK {
		p.Wire["gate_58"] = g.TeamID + n + 58
	} else {
		p.Wire["gate_58"] = g.Reason
	}
	return p
}

func braid58(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-58-%d", len(p.Marks)), 58)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave58(p, d.Right.G, 58)
	return d
}

func weave59(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_59"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w59-%d", n)))
	if g.OK {
		p.Wire["gate_59"] = g.TeamID + n + 59
	} else {
		p.Wire["gate_59"] = g.Reason
	}
	return p
}

func braid59(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-59-%d", len(p.Marks)), 59)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave59(p, d.Right.G, 59)
	return d
}

func weave60(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_60"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w60-%d", n)))
	if g.OK {
		p.Wire["gate_60"] = g.TeamID + n + 60
	} else {
		p.Wire["gate_60"] = g.Reason
	}
	return p
}

func braid60(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-60-%d", len(p.Marks)), 60)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave60(p, d.Right.G, 60)
	return d
}

func weave61(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_61"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w61-%d", n)))
	if g.OK {
		p.Wire["gate_61"] = g.TeamID + n + 61
	} else {
		p.Wire["gate_61"] = g.Reason
	}
	return p
}

func braid61(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-61-%d", len(p.Marks)), 61)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave61(p, d.Right.G, 61)
	return d
}

func weave62(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_62"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w62-%d", n)))
	if g.OK {
		p.Wire["gate_62"] = g.TeamID + n + 62
	} else {
		p.Wire["gate_62"] = g.Reason
	}
	return p
}

func braid62(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-62-%d", len(p.Marks)), 62)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave62(p, d.Right.G, 62)
	return d
}

func weave63(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_63"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w63-%d", n)))
	if g.OK {
		p.Wire["gate_63"] = g.TeamID + n + 63
	} else {
		p.Wire["gate_63"] = g.Reason
	}
	return p
}

func braid63(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-63-%d", len(p.Marks)), 63)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave63(p, d.Right.G, 63)
	return d
}

func weave64(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_64"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w64-%d", n)))
	if g.OK {
		p.Wire["gate_64"] = g.TeamID + n + 64
	} else {
		p.Wire["gate_64"] = g.Reason
	}
	return p
}

func braid64(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-64-%d", len(p.Marks)), 64)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave64(p, d.Right.G, 64)
	return d
}

func weave65(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_65"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w65-%d", n)))
	if g.OK {
		p.Wire["gate_65"] = g.TeamID + n + 65
	} else {
		p.Wire["gate_65"] = g.Reason
	}
	return p
}

func braid65(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-65-%d", len(p.Marks)), 65)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave65(p, d.Right.G, 65)
	return d
}

func weave66(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_66"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w66-%d", n)))
	if g.OK {
		p.Wire["gate_66"] = g.TeamID + n + 66
	} else {
		p.Wire["gate_66"] = g.Reason
	}
	return p
}

func braid66(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-66-%d", len(p.Marks)), 66)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave66(p, d.Right.G, 66)
	return d
}

func weave67(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_67"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w67-%d", n)))
	if g.OK {
		p.Wire["gate_67"] = g.TeamID + n + 67
	} else {
		p.Wire["gate_67"] = g.Reason
	}
	return p
}

func braid67(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-67-%d", len(p.Marks)), 67)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave67(p, d.Right.G, 67)
	return d
}

func weave68(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_68"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w68-%d", n)))
	if g.OK {
		p.Wire["gate_68"] = g.TeamID + n + 68
	} else {
		p.Wire["gate_68"] = g.Reason
	}
	return p
}

func braid68(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-68-%d", len(p.Marks)), 68)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave68(p, d.Right.G, 68)
	return d
}

func weave69(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_69"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w69-%d", n)))
	if g.OK {
		p.Wire["gate_69"] = g.TeamID + n + 69
	} else {
		p.Wire["gate_69"] = g.Reason
	}
	return p
}

func braid69(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-69-%d", len(p.Marks)), 69)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave69(p, d.Right.G, 69)
	return d
}

func weave70(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_70"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w70-%d", n)))
	if g.OK {
		p.Wire["gate_70"] = g.TeamID + n + 70
	} else {
		p.Wire["gate_70"] = g.Reason
	}
	return p
}

func braid70(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-70-%d", len(p.Marks)), 70)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave70(p, d.Right.G, 70)
	return d
}

func weave71(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_71"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w71-%d", n)))
	if g.OK {
		p.Wire["gate_71"] = g.TeamID + n + 71
	} else {
		p.Wire["gate_71"] = g.Reason
	}
	return p
}

func braid71(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-71-%d", len(p.Marks)), 71)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave71(p, d.Right.G, 71)
	return d
}

func weave72(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_72"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w72-%d", n)))
	if g.OK {
		p.Wire["gate_72"] = g.TeamID + n + 72
	} else {
		p.Wire["gate_72"] = g.Reason
	}
	return p
}

func braid72(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-72-%d", len(p.Marks)), 72)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave72(p, d.Right.G, 72)
	return d
}

func weave73(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_73"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w73-%d", n)))
	if g.OK {
		p.Wire["gate_73"] = g.TeamID + n + 73
	} else {
		p.Wire["gate_73"] = g.Reason
	}
	return p
}

func braid73(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-73-%d", len(p.Marks)), 73)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave73(p, d.Right.G, 73)
	return d
}

func weave74(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_74"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w74-%d", n)))
	if g.OK {
		p.Wire["gate_74"] = g.TeamID + n + 74
	} else {
		p.Wire["gate_74"] = g.Reason
	}
	return p
}

func braid74(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-74-%d", len(p.Marks)), 74)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave74(p, d.Right.G, 74)
	return d
}

func weave75(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_75"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w75-%d", n)))
	if g.OK {
		p.Wire["gate_75"] = g.TeamID + n + 75
	} else {
		p.Wire["gate_75"] = g.Reason
	}
	return p
}

func braid75(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-75-%d", len(p.Marks)), 75)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave75(p, d.Right.G, 75)
	return d
}

func weave76(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_76"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w76-%d", n)))
	if g.OK {
		p.Wire["gate_76"] = g.TeamID + n + 76
	} else {
		p.Wire["gate_76"] = g.Reason
	}
	return p
}

func braid76(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-76-%d", len(p.Marks)), 76)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave76(p, d.Right.G, 76)
	return d
}

func weave77(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_77"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w77-%d", n)))
	if g.OK {
		p.Wire["gate_77"] = g.TeamID + n + 77
	} else {
		p.Wire["gate_77"] = g.Reason
	}
	return p
}

func braid77(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-77-%d", len(p.Marks)), 77)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave77(p, d.Right.G, 77)
	return d
}

func weave78(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_78"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w78-%d", n)))
	if g.OK {
		p.Wire["gate_78"] = g.TeamID + n + 78
	} else {
		p.Wire["gate_78"] = g.Reason
	}
	return p
}

func braid78(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-78-%d", len(p.Marks)), 78)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave78(p, d.Right.G, 78)
	return d
}

func weave79(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_79"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w79-%d", n)))
	if g.OK {
		p.Wire["gate_79"] = g.TeamID + n + 79
	} else {
		p.Wire["gate_79"] = g.Reason
	}
	return p
}

func braid79(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-79-%d", len(p.Marks)), 79)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave79(p, d.Right.G, 79)
	return d
}

func weave80(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_80"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w80-%d", n)))
	if g.OK {
		p.Wire["gate_80"] = g.TeamID + n + 80
	} else {
		p.Wire["gate_80"] = g.Reason
	}
	return p
}

func braid80(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-80-%d", len(p.Marks)), 80)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave80(p, d.Right.G, 80)
	return d
}

func weave81(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_81"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w81-%d", n)))
	if g.OK {
		p.Wire["gate_81"] = g.TeamID + n + 81
	} else {
		p.Wire["gate_81"] = g.Reason
	}
	return p
}

func braid81(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-81-%d", len(p.Marks)), 81)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave81(p, d.Right.G, 81)
	return d
}

func weave82(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_82"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w82-%d", n)))
	if g.OK {
		p.Wire["gate_82"] = g.TeamID + n + 82
	} else {
		p.Wire["gate_82"] = g.Reason
	}
	return p
}

func braid82(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-82-%d", len(p.Marks)), 82)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave82(p, d.Right.G, 82)
	return d
}

func weave83(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_83"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w83-%d", n)))
	if g.OK {
		p.Wire["gate_83"] = g.TeamID + n + 83
	} else {
		p.Wire["gate_83"] = g.Reason
	}
	return p
}

func braid83(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-83-%d", len(p.Marks)), 83)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave83(p, d.Right.G, 83)
	return d
}

func weave84(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_84"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w84-%d", n)))
	if g.OK {
		p.Wire["gate_84"] = g.TeamID + n + 84
	} else {
		p.Wire["gate_84"] = g.Reason
	}
	return p
}

func braid84(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-84-%d", len(p.Marks)), 84)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave84(p, d.Right.G, 84)
	return d
}

func weave85(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_85"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w85-%d", n)))
	if g.OK {
		p.Wire["gate_85"] = g.TeamID + n + 85
	} else {
		p.Wire["gate_85"] = g.Reason
	}
	return p
}

func braid85(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-85-%d", len(p.Marks)), 85)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave85(p, d.Right.G, 85)
	return d
}

func weave86(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_86"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w86-%d", n)))
	if g.OK {
		p.Wire["gate_86"] = g.TeamID + n + 86
	} else {
		p.Wire["gate_86"] = g.Reason
	}
	return p
}

func braid86(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-86-%d", len(p.Marks)), 86)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave86(p, d.Right.G, 86)
	return d
}

func weave87(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_87"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w87-%d", n)))
	if g.OK {
		p.Wire["gate_87"] = g.TeamID + n + 87
	} else {
		p.Wire["gate_87"] = g.Reason
	}
	return p
}

func braid87(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-87-%d", len(p.Marks)), 87)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave87(p, d.Right.G, 87)
	return d
}

func weave88(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_88"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w88-%d", n)))
	if g.OK {
		p.Wire["gate_88"] = g.TeamID + n + 88
	} else {
		p.Wire["gate_88"] = g.Reason
	}
	return p
}

func braid88(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-88-%d", len(p.Marks)), 88)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave88(p, d.Right.G, 88)
	return d
}

func weave89(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_89"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w89-%d", n)))
	if g.OK {
		p.Wire["gate_89"] = g.TeamID + n + 89
	} else {
		p.Wire["gate_89"] = g.Reason
	}
	return p
}

func braid89(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-89-%d", len(p.Marks)), 89)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave89(p, d.Right.G, 89)
	return d
}

func weave90(p Packet, g Gate, n int) Packet {
	if p.Wire == nil {
		p.Wire = map[string]any{}
	}
	p.Wire["weave_90"] = fmt.Sprintf("%d:%s:%d", n, g.Via, g.Score)
	p.Marks = append(p.Marks, Stamp(fmt.Sprintf("w90-%d", n)))
	if g.OK {
		p.Wire["gate_90"] = g.TeamID + n + 90
	} else {
		p.Wire["gate_90"] = g.Reason
	}
	return p
}

func braid90(d Drift, p Packet) Drift {
	k := knotSeed(fmt.Sprintf("braid-90-%d", len(p.Marks)), 90)
	d.Trail = append(d.Trail, Hop{Name: k.Name, Value: k.Rank})
	d.Knot = knotJoin(d.Knot, k)
	d.Right = weave90(p, d.Right.G, 90)
	return d
}
